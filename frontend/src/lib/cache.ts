import type { JSONValue } from './fetcher'

const cache = new Map<string, JSONValue>()

export function makeKey(url: string, body: JSONValue) {
	return `${url}|${JSON.stringify(body)}`
}

export function get<T = unknown>(key: string): T | undefined {
	return cache.get(key) as T | undefined
}

export function set<T = unknown>(key: string, value: T) {
	cache.set(key, value as JSONValue)
}
