export type JSONValue = string | number | boolean | null | JSONValue[] | { [k: string]: JSONValue };

export async function fetchJSON<T = unknown>(
	url: string,
	options: RequestInit & { signal?: AbortSignal } = {}
): Promise<T> {
	const res = await fetch(url, {
		...options,
		headers: {
			'Content-Type': 'application/json',
			...(options.headers || {}),
		},
	});
	if (!res.ok) {
        // Try to extract a useful error message from JSON { detail }
        try {
            const data = await res.json()
            const detail = (data && (data.detail || data.message)) as string | undefined
            throw new Error(detail || `Request failed with ${res.status}`)
        } catch {
            const text = await res.text().catch(() => '')
            throw new Error(text || `Request failed with ${res.status}`)
        }
	}
	return (await res.json()) as T
}

export function debounce<F extends (...args: any[]) => void>(fn: F, wait: number) {
	let t: number | undefined
	return (...args: Parameters<F>) => {
		if (t) window.clearTimeout(t)
		t = window.setTimeout(() => fn(...args), wait)
	}
}
