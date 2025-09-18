import { useEffect, useMemo, useRef, useState } from 'react'
import { SearchBar } from './components/SearchBar'
import { Controls } from './components/Controls'
import { ResultCard } from './components/ResultCard'
import { Skeleton } from './components/Skeleton'
import { debounce, fetchJSON } from './lib/fetcher'
import { Toast } from './components/Toast'
import { get as cacheGet, set as cacheSet, makeKey } from './lib/cache'

interface SearchHit { id: string; text: string; score: number }
interface SearchResponse { results: SearchHit[] }

type Metric = 'cosine' | 'dot' | 'euclidean'

function App() {
	const [query, setQuery] = useState('')
	const [metric, setMetric] = useState<Metric>('cosine')
	const [k, setK] = useState(10)
	const [loading, setLoading] = useState(false)
	const [error, setError] = useState<string | null>(null)
	const [results, setResults] = useState<SearchHit[]>([])
	const abortRef = useRef<AbortController | null>(null)

	const doSearch = async (q: string) => {
		if (!q.trim()) {
			setResults([])
			return
		}
		const url = 'http://localhost:8000/search'
		const body = { query: q, k, metric }
		const key = makeKey(url, body)
		const cached = cacheGet<SearchResponse>(key)
		if (cached) {
			setResults(cached.results)
			return
		}
		abortRef.current?.abort()
		const controller = new AbortController()
		abortRef.current = controller
		setLoading(true)
		setError(null)
		try {
			const data = await fetchJSON<SearchResponse>(url, {
				method: 'POST',
				body: JSON.stringify(body),
				signal: controller.signal,
			})
			cacheSet(key, data)
			setResults(data.results)
		} catch (e: any) {
			if (e?.name === 'AbortError') return
			setError(e?.message || 'Request failed')
			setResults([])
		} finally {
			setLoading(false)
		}
	}

const debouncedSearch = useMemo(() => debounce(doSearch, 280), [k, metric])

// Load all posts on mount for empty state
useEffect(() => {
    (async () => {
        try {
            const data = await fetchJSON<SearchResponse>('http://localhost:8000/posts')
            setResults(data.results)
        } catch (e: any) {
            setError(e?.message || 'Failed to load posts')
        }
    })()
}, [])

// Immediately trigger a search when metric or k change (using latest state)
useEffect(() => {
    // If no query, keep showing full list; otherwise search immediately
    if (query.trim()) {
        void doSearch(query)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
}, [metric, k])

	return (
		<div className="min-h-screen bg-neutral-950 text-neutral-100">
			{error && <Toast message={error} />}
			<header className="sticky top-0 z-10 border-b border-neutral-800 bg-neutral-950/80 backdrop-blur">
				<div className="container flex items-center justify-between py-4">
					<div className="flex items-center">
						<h1 className="text-xl font-semibold tracking-tight shine-animation">Custom Vector Search</h1>
					</div>
                    <Controls
                        k={k}
                        onKChange={(val) => {
                            setK(val)
                        }}
                        metric={metric}
                        onMetricChange={(m) => {
                            setMetric(m)
                        }}
                    />
				</div>
			</header>
			<main className="container py-8">
				<div className="mx-auto max-w-3xl space-y-6">
					<SearchBar
						value={query}
						onChange={(v) => {
							setQuery(v)
							debouncedSearch(v)
						}}
						onSubmit={() => doSearch(query)}
					/>
					<div className="grid grid-cols-1 gap-4 md:grid-cols-2">
						{loading && (
							<>
								{Array.from({ length: 6 }).map((_, i) => (
									<Skeleton key={i} />
								))}
							</>
						)}
						{!loading && results.length === 0 && query.trim() && (
							<div className="col-span-full rounded-xl border border-neutral-800 bg-neutral-900 p-4 text-sm text-neutral-400">
								No results
							</div>
						)}
						{!loading && results.map((r) => (
							<ResultCard key={r.id + r.score} id={r.id} text={r.text} score={r.score} query={query} />
						))}
					</div>
				</div>
			</main>
		</div>
	)
}

export default App
