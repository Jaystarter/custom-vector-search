export function cn(...classes: Array<string | false | null | undefined>) {
	return classes.filter(Boolean).join(' ')
}

export function clamp(n: number, min: number, max: number) {
	return Math.max(min, Math.min(max, n))
}
