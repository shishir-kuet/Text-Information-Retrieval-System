import { cn } from "../../lib/utils"

type Option = { label: string; value: string }

type SelectProps = {
  value: string
  onChange: (value: string) => void
  options: Option[]
  className?: string
}

export function Select({ value, onChange, options, className }: SelectProps) {
  return (
    <select
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className={cn(
        "h-11 rounded-xl border border-white/20 bg-[var(--color-surface)] px-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]",
        className,
      )}
    >
      {options.map((option) => (
        <option key={option.value} value={option.value} className="text-black">
          {option.label}
        </option>
      ))}
    </select>
  )
}
