export function highlight(text: string, query: string) {
	const q = query.trim()
	if (!q) return text
	try {
		const escaped = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
		const re = new RegExp(`(${escaped})`, 'ig')
		return text.split(re).map((part, i) =>
			i % 2 === 1 ? `<mark class="bg-yellow-300/20 text-yellow-200">${part}</mark>` : part
		).join('')
	} catch {
		return text
	}
}
