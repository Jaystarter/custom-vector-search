import { highlight } from '../lib/highlight'

interface Props {
	id: string
	text: string
	score: number
	query?: string
}

export function ResultCard({ id, text, score, query }: Props) {
	const html = highlight(text, query ?? '')
	return (
		<div className="rounded-xl border border-neutral-800 bg-neutral-900 p-4">
			<div className="flex items-start justify-between gap-4">
				<div className="truncate text-sm text-neutral-400" title={id}>
					{id}
				</div>
				<div className="text-xs font-mono text-neutral-400">{score.toFixed(4)}</div>
			</div>
			<p className="prose prose-invert mt-2 leading-snug text-neutral-100" dangerouslySetInnerHTML={{ __html: html }} />
		</div>
	)
}
