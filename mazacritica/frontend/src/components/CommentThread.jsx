import './CommentThread.css'

/* eslint-disable react/prop-types -- los comentarios llegan de la API */
function CommentItem({ comment, canReply, onReply, replyForm }) {
  return (
    <article className={comment.parent ? 'comment comment-reply' : 'comment'}>
      <div className="comment-avatar">{(comment.nickname || '?').slice(0, 2).toUpperCase()}</div>
      <div className="comment-body">
        <div className="comment-meta">
          <strong>{comment.nickname}</strong>
          <span>{comment.status === 'pending' ? 'Pendiente de moderación' : 'Visible'}</span>
        </div>
        <p>{comment.body}</p>
        {canReply && (
          <div className="comment-actions">
            <button type="button" onClick={() => onReply(comment.id)}>Responder</button>
          </div>
        )}
        {replyForm}
        {(comment.replies || []).map((reply) => (
          <CommentItem comment={reply} canReply={false} key={reply.id} onReply={onReply} />
        ))}
      </div>
    </article>
  )
}

export default function CommentThread({
  comments,
  account,
  commentBody,
  replyTo,
  replyBody,
  onCommentBody,
  onReplyBody,
  onSubmitComment,
  onSubmitReply,
  onReply,
  onRequestAuth,
}) {
  return (
    <section className="comments-section" aria-labelledby="comments-title">
      <div className="detail-section-heading">
        <div>
          <span className="eyebrow">CONVERSACIÓN</span>
          <h2 id="comments-title">{comments.length} comentarios visibles</h2>
        </div>
      </div>
      <div className="comment-list">
        {comments.map((comment) => (
          <CommentItem
            key={comment.id}
            comment={comment}
            canReply={!comment.parent}
            onReply={onReply}
            replyForm={replyTo === comment.id ? (
              <form onSubmit={onSubmitReply}>
                <label>
                  Respuesta directa
                  <textarea value={replyBody} onChange={(event) => onReplyBody(event.target.value)} required />
                </label>
                <button type="submit">Publicar respuesta</button>
              </form>
            ) : null}
          />
        ))}
      </div>
      {account ? (
        <form className="comment-composer" aria-label="Nuevo comentario" onSubmit={onSubmitComment}>
          <label>
            Comentario
            <textarea value={commentBody} onChange={(event) => onCommentBody(event.target.value)} required />
          </label>
          <button type="submit">Publicar comentario</button>
        </form>
      ) : (
        <div className="comment-gate">
          <span className="comment-gate-mark">◌</span>
          <div>
            <strong>La conversación empieza con contexto.</strong>
            <p>Ingresa para comentar con tu nickname. Las notas editoriales solo las publica MazaCrítica.</p>
          </div>
          <button className="join-button" type="button" onClick={onRequestAuth}>Comentar</button>
        </div>
      )}
    </section>
  )
}
/* eslint-enable react/prop-types */
