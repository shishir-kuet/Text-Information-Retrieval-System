import type { InputHTMLAttributes } from "react"
import { cn } from "../../lib/utils"

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "w-full rounded-xl border border-white/20 bg-[var(--color-surface)] px-4 py-3 text-sm text-white placeholder:text-white/60 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]",
        className,
      )}
      {...props}
    />
  )
}
