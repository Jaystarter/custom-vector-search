import { useEffect, useRef, useState } from 'react'

interface Props {
	value: string
	onChange: (v: string) => void
	onSubmit: () => void
}

export function SearchBar({ value, onChange, onSubmit }: Props) {
	const ref = useRef<HTMLInputElement>(null)
	const [local, setLocal] = useState(value)

	useEffect(() => setLocal(value), [value])

	useEffect(() => {
		const onKey = (e: KeyboardEvent) => {
			if (e.key === '/' && document.activeElement !== ref.current) {
				e.preventDefault()
				ref.current?.focus()
			}
		}
		document.addEventListener('keydown', onKey)
		return () => document.removeEventListener('keydown', onKey)
	}, [])

	return (
		<div className="flex items-center gap-2 rounded-2xl border border-neutral-800 bg-neutral-900 px-4 py-3">
			<input
				ref={ref}
				value={local}
				onChange={(e) => {
					setLocal(e.target.value)
					onChange(e.target.value)
				}}
				onKeyDown={(e) => {
					if (e.key === 'Enter') onSubmit()
					if (e.key === 'Escape') {
						setLocal('')
						onChange('')
						ref.current?.blur()
					}
				}}
				placeholder="Search blog posts... (press / to focus)"
				className="w-full bg-transparent outline-none placeholder:text-neutral-500"
			/>
		</div>
	)
}
