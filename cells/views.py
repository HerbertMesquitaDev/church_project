from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Cell, CellMembership, CellPost, CellPostReaction


def _get_membership(user, cell):
    try:
        return CellMembership.objects.get(user=user, cell=cell)
    except CellMembership.DoesNotExist:
        return None


# ── Public cell list ──────────────────────────────────────
@login_required
def cell_list(request):
    cells     = Cell.objects.filter(active=True)
    my_cells  = CellMembership.objects.filter(
        user=request.user, status='approved'
    ).select_related('cell')
    pending   = CellMembership.objects.filter(
        user=request.user, status='pending'
    ).values_list('cell_id', flat=True)

    return render(request, 'cells/cell_list.html', {
        'cells':    cells,
        'my_cells': [m.cell for m in my_cells],
        'pending':  list(pending),
    })


# ── Cell detail / mural ───────────────────────────────────
@login_required
def cell_detail(request, pk):
    cell       = get_object_or_404(Cell, pk=pk, active=True)
    membership = _get_membership(request.user, cell)

    # Only approved members or staff can see the mural
    is_member = membership and membership.status == 'approved'
    is_leader = is_member and membership.role == 'leader'
    is_staff  = request.user.is_staff or request.user.is_superuser

    if not (is_member or is_staff):
        return render(request, 'cells/cell_preview.html', {
            'cell':       cell,
            'membership': membership,
        })

    # Handle new post
    if request.method == 'POST' and (is_member or is_staff):
        content   = request.POST.get('content', '').strip()
        post_type = request.POST.get('post_type', 'message')
        file_obj  = request.FILES.get('file')

        # Only leader/staff can post notices
        if post_type == 'notice' and not (is_leader or is_staff):
            post_type = 'message'

        if content:
            post = CellPost.objects.create(
                cell=cell,
                author=request.user,
                post_type=post_type,
                content=content,
                file=file_obj,
            )
            # Leaders can pin their notices directly
            if post_type == 'notice' and (is_leader or is_staff):
                post.pinned = True
                post.save()
            messages.success(request, 'Mensagem publicada!')
        return redirect('cell_detail', pk=pk)

    posts   = cell.posts.select_related('author').prefetch_related('reactions')
    members = cell.memberships.filter(status='approved').select_related('user')
    pending_count = cell.memberships.filter(status='pending').count() if (is_leader or is_staff) else 0

    # Build reaction counts per post
    EMOJIS = ['🙏', '❤️', '👏', '🔥', '✝️']
    post_data = []
    for post in posts:
        reacts = {}
        for emoji in EMOJIS:
            count = post.reactions.filter(emoji=emoji).count()
            user_reacted = post.reactions.filter(user=request.user, emoji=emoji).exists()
            reacts[emoji] = {'count': count, 'user_reacted': user_reacted}
        post_data.append({'post': post, 'reactions': reacts})

    return render(request, 'cells/cell_detail.html', {
        'cell':          cell,
        'membership':    membership,
        'is_member':     is_member,
        'is_leader':     is_leader or is_staff,
        'is_staff':      is_staff,
        'post_data':     post_data,
        'members':       members,
        'pending_count': pending_count,
        'emojis':        EMOJIS,
    })


# ── Join / leave ──────────────────────────────────────────
@login_required
def cell_join(request, pk):
    cell       = get_object_or_404(Cell, pk=pk, active=True)
    membership = _get_membership(request.user, cell)

    if membership:
        if membership.status == 'left' or membership.status == 'rejected':
            membership.status = 'pending'
            membership.save()
            messages.success(request, 'Pedido de entrada enviado! Aguarde a aprovação do líder.')
        else:
            messages.info(request, 'Você já faz parte deste grupo ou tem um pedido pendente.')
    else:
        CellMembership.objects.create(cell=cell, user=request.user, status='pending')
        messages.success(request, 'Pedido de entrada enviado! Aguarde a aprovação do líder.')
    return redirect('cell_detail', pk=pk)


@login_required
def cell_leave(request, pk):
    cell       = get_object_or_404(Cell, pk=pk)
    membership = CellMembership.objects.filter(cell=cell, user=request.user, status='approved').first()
    if not membership:
        messages.error(request, 'Você não é membro ativo deste grupo.')
        return redirect('cell_detail', pk=pk)
    if request.method == 'POST':
        membership.status = 'left'
        membership.save()
        messages.success(request, f'Você saiu do grupo {cell.name}.')
        return redirect('cell_list')
    return render(request, 'cells/cell_leave.html', {'cell': cell})


# ── Leader: manage membership requests ───────────────────
@login_required
def cell_manage_members(request, pk):
    cell       = get_object_or_404(Cell, pk=pk, active=True)
    membership = _get_membership(request.user, cell)
    is_leader  = (membership and membership.role == 'leader') or \
                  request.user.is_staff or request.user.is_superuser

    if not is_leader:
        messages.error(request, 'Acesso restrito ao líder.')
        return redirect('cell_detail', pk=pk)

    if request.method == 'POST':
        action    = request.POST.get('action')
        member_id = request.POST.get('membership_id')
        try:
            m = CellMembership.objects.get(pk=member_id, cell=cell)
            if action == 'approve':
                m.status = 'approved'
                m.save()
                messages.success(request, f'{m.user.get_full_name() or m.user.username} aprovado(a)!')
            elif action == 'reject':
                m.status = 'rejected'
                m.save()
                messages.info(request, 'Pedido recusado.')
            elif action == 'remove':
                m.status = 'left'
                m.save()
                messages.info(request, 'Membro removido do grupo.')
            elif action == 'make_leader':
                m.role = 'leader'
                m.save()
            elif action == 'make_member':
                m.role = 'member'
                m.save()
        except CellMembership.DoesNotExist:
            pass
        return redirect('cell_manage_members', pk=pk)

    pending  = cell.memberships.filter(status='pending').select_related('user')
    approved = cell.memberships.filter(status='approved').select_related('user')
    return render(request, 'cells/cell_manage_members.html', {
        'cell':     cell,
        'pending':  pending,
        'approved': approved,
    })


# ── Post actions ──────────────────────────────────────────
@login_required
def cell_delete_post(request, pk, post_pk):
    cell = get_object_or_404(Cell, pk=pk)
    post = get_object_or_404(CellPost, pk=post_pk, cell=cell)
    membership = _get_membership(request.user, cell)
    is_leader  = (membership and membership.role == 'leader') or \
                  request.user.is_staff or request.user.is_superuser

    if request.user == post.author or is_leader:
        post.delete()
        messages.success(request, 'Mensagem removida.')
    return redirect('cell_detail', pk=pk)


@login_required
def cell_pin_post(request, pk, post_pk):
    cell = get_object_or_404(Cell, pk=pk)
    post = get_object_or_404(CellPost, pk=post_pk, cell=cell)
    membership = _get_membership(request.user, cell)
    is_leader  = (membership and membership.role == 'leader') or \
                  request.user.is_staff or request.user.is_superuser

    if is_leader:
        post.pinned = not post.pinned
        post.save()
    return redirect('cell_detail', pk=pk)


@login_required
@require_POST
def cell_react(request, pk, post_pk):
    cell = get_object_or_404(Cell, pk=pk)
    post = get_object_or_404(CellPost, pk=post_pk, cell=cell)
    membership = _get_membership(request.user, cell)
    is_staff   = request.user.is_staff or request.user.is_superuser

    if not (membership and membership.status == 'approved') and not is_staff:
        return JsonResponse({'error': 'unauthorized'}, status=403)

    emoji = request.POST.get('emoji', '🙏')
    existing = CellPostReaction.objects.filter(post=post, user=request.user, emoji=emoji).first()
    if existing:
        existing.delete()
        reacted = False
    else:
        CellPostReaction.objects.create(post=post, user=request.user, emoji=emoji)
        reacted = True

    count = CellPostReaction.objects.filter(post=post, emoji=emoji).count()
    return JsonResponse({'count': count, 'reacted': reacted})
