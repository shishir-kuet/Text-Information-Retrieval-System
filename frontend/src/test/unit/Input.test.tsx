import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Input } from '../../components/ui/input';

describe('Input', () => {
  it('renders an input element', () => {
    render(<Input />);
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('renders with placeholder text', () => {
    render(<Input placeholder="Search here…" />);
    expect(screen.getByPlaceholderText('Search here…')).toBeInTheDocument();
  });

  it('calls onChange with new value', () => {
    const onChange = vi.fn();
    render(<Input value="" onChange={onChange} />);
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'hello' } });
    expect(onChange).toHaveBeenCalledTimes(1);
  });

  it('reflects controlled value', () => {
    render(<Input value="test value" onChange={vi.fn()} />);
    expect(screen.getByRole('textbox')).toHaveValue('test value');
  });

  it('is disabled when disabled prop passed', () => {
    render(<Input disabled />);
    expect(screen.getByRole('textbox')).toBeDisabled();
  });

  it('merges custom className', () => {
    render(<Input className="pl-12" />);
    expect(screen.getByRole('textbox')).toHaveClass('pl-12');
  });

  it('renders as password type', () => {
    render(<Input type="password" data-testid="pwd" />);
    expect(screen.getByTestId('pwd')).toHaveAttribute('type', 'password');
  });
});
