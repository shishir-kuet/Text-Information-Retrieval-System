import type { ButtonHTMLAttributes } from "react"
import { cn } from "../../lib/utils"

const styles = {
  base: "inline-flex items-center justify-center rounded-xl px-5 py-3 text-sm font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)] disabled:cursor-not-allowed disabled:opacity-60",
  solid: "bg-[var(--color-accent)] text-white hover:opacity-90",
  ghost: "border border-white/20 text-white hover:border-white/50 hover:bg-white/5",
  outline: "border border-[var(--color-accent)] text-white hover:bg-[var(--color-accent)]/10",
}

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "solid" | "ghost" | "outline"
}

export function Button({ className, variant = "solid", ...props }: ButtonProps) {
  return <button className={cn(styles.base, styles[variant], className)} {...props} />
}
