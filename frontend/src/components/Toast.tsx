import * as ToastPrimitive from '@radix-ui/react-toast'
import { useState } from 'react'

export function Toast({ message }: { message: string }) {
	const [open, setOpen] = useState(true)
	return (
		<ToastPrimitive.Provider>
			<ToastPrimitive.Root open={open} onOpenChange={setOpen} className="fixed bottom-4 right-4 rounded-lg border border-red-900 bg-red-950 px-3 py-2 text-sm text-red-200 shadow-lg">
				{message}
			</ToastPrimitive.Root>
			<ToastPrimitive.Viewport />
		</ToastPrimitive.Provider>
	)
}
