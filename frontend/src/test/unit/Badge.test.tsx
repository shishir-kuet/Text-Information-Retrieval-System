import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Badge } from '../../components/ui/badge';

describe('Badge', () => {
  it('renders children text', () => {
    render(<Badge>CS</Badge>);
    expect(screen.getByText('CS')).toBeInTheDocument();
  });

  it('applies default variant class', () => {
    render(<Badge>Default</Badge>);
    expect(screen.getByText('Default')).toHaveClass('bg-white/10');
  });

  it('applies outline variant class', () => {
    render(<Badge variant="outline">Outline</Badge>);
    expect(screen.getByText('Outline')).toHaveClass('border-white/20');
  });

  it('applies secondary variant class', () => {
    render(<Badge variant="secondary">Secondary</Badge>);
    expect(screen.getByText('Secondary')).toHaveClass('bg-white/5');
  });

  it('merges custom className', () => {
    render(<Badge className="text-xs">Tag</Badge>);
    expect(screen.getByText('Tag')).toHaveClass('text-xs');
  });
});
