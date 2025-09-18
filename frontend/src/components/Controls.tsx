interface Props {
	k: number
	onKChange: (k: number) => void
	metric: 'cosine' | 'dot' | 'euclidean'
	onMetricChange: (m: 'cosine' | 'dot' | 'euclidean') => void
}

export function Controls({ k, onKChange, metric, onMetricChange }: Props) {
	return (
		<div className="flex items-center gap-2 rounded-xl border border-neutral-800 bg-neutral-900/70 px-2 py-1 backdrop-blur">
			<div className="flex items-center gap-2">
				<span className="text-[10px] uppercase tracking-wide text-neutral-400">metric</span>
				<select
					aria-label="distance metric"
					value={metric}
					onChange={(e) => onMetricChange(e.target.value as any)}
					className="rounded-lg border border-neutral-800 bg-neutral-900 px-3 py-1.5 text-sm text-neutral-100 outline-none focus:ring-2 focus:ring-neutral-700"
				>
					<option value="cosine">cosine</option>
					<option value="dot">dot</option>
					<option value="euclidean">euclidean</option>
				</select>
			</div>
			<div className="h-5 w-px bg-neutral-800" />
			<div className="flex items-center gap-2">
				<span className="text-[10px] uppercase tracking-wide text-neutral-400">top k</span>
				<select
					aria-label="top k"
					value={k}
					onChange={(e) => onKChange(parseInt(e.target.value) || 10)}
					className="rounded-lg border border-neutral-800 bg-neutral-900 px-3 py-1.5 text-sm text-neutral-100 outline-none focus:ring-2 focus:ring-neutral-700"
				>
					{[3, 5, 10, 20].map((n) => (
						<option key={n} value={n}>
							{n}
						</option>
					))}
				</select>
			</div>
		</div>
	)
}
