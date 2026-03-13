import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import React from 'react';
import Home from '../../pages/Home';

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router')>();
  return { ...actual, useNavigate: () => mockNavigate };
});

// Mock motion/react — replace animated elements with plain HTML equivalents
vi.mock('motion/react', () => ({
  motion: new Proxy({} as Record<string, unknown>, {
    get: (_target, tag: string) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return ({ children, initial: _i, animate: _a, transition: _t, ...rest }: any) =>
        React.createElement(tag, rest, children);
    },
  }),
}));

const renderHome = () => render(<MemoryRouter><Home /></MemoryRouter>);

describe('Home page — layout', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    renderHome();
  });

  it('renders the TIRS brand name', () => {
    expect(screen.getAllByText('TIRS').length).toBeGreaterThan(0);
  });

  it('renders the hero heading', () => {
    expect(screen.getByText('Text Information')).toBeInTheDocument();
    expect(screen.getByText('Retrieval System')).toBeInTheDocument();
  });

  it('renders the hero subtitle', () => {
    expect(screen.getByText(/Search through thousands of indexed documents/i)).toBeInTheDocument();
  });

  it('renders the Login button', () => {
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  });

  it('renders the Get Started button', () => {
    expect(screen.getByRole('button', { name: /get started/i })).toBeInTheDocument();
  });

  it('renders the search input', () => {
    expect(screen.getByPlaceholderText(/search books, topics, passages/i)).toBeInTheDocument();
  });

  it('renders the Search submit button', () => {
    expect(screen.getByRole('button', { name: /^search$/i })).toBeInTheDocument();
  });

  it('renders the Why Choose TIRS section', () => {
    expect(screen.getByText(/why choose/i)).toBeInTheDocument();
  });

  it('renders all three feature cards', () => {
    expect(screen.getByText('Lightning Fast')).toBeInTheDocument();
    expect(screen.getByText('Smart Results')).toBeInTheDocument();
    expect(screen.getByText('Secure & Private')).toBeInTheDocument();
  });

  it('renders the footer copyright', () => {
    expect(screen.getByText(/© 2026 Text Information Retrieval System/i)).toBeInTheDocument();
  });
});

describe('Home page — search interaction', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
  });

  it('updates input value as user types', async () => {
    renderHome();
    const input = screen.getByPlaceholderText(/search books, topics, passages/i);
    fireEvent.change(input, { target: { value: 'philosophy' } });
    expect(input).toHaveValue('philosophy');
  });

  it('submitting with a query navigates to /results', async () => {
    renderHome();
    const input = screen.getByPlaceholderText(/search books, topics, passages/i);
    fireEvent.change(input, { target: { value: 'stoicism' } });
    expect(input).toHaveValue('stoicism'); // confirm DOM value updated
    const submitBtn = screen.getByRole('button', { name: /^search$/i });
    await userEvent.click(submitBtn);
    expect(mockNavigate).toHaveBeenCalledWith('/results?q=stoicism&k=5');
  });

  it('submitting with empty query does NOT navigate', async () => {
    const user = userEvent.setup();
    renderHome();
    const input = screen.getByPlaceholderText(/search books, topics, passages/i);
    await user.click(input);
    await user.keyboard('{Enter}');
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('submitting with whitespace-only query does NOT navigate', async () => {
    const user = userEvent.setup();
    renderHome();
    const input = screen.getByPlaceholderText(/search books, topics, passages/i);
    await user.type(input, '   {Enter}');
    expect(mockNavigate).not.toHaveBeenCalled();
  });
});

describe('Home page — navigation buttons', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    renderHome();
  });

  it('Login button navigates to /login', async () => {
    await userEvent.click(screen.getByRole('button', { name: /login/i }));
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  it('Get Started button navigates to /register', async () => {
    await userEvent.click(screen.getByRole('button', { name: /get started/i }));
    expect(mockNavigate).toHaveBeenCalledWith('/register');
  });
});

describe('Home page — top-k selection', () => {
  it('default topK value is 5', () => {
    renderHome();
    // '5' appears in both the SelectTrigger span and the hidden <option>
    expect(screen.getAllByText('5').length).toBeGreaterThanOrEqual(1);
  });

  it('navigates with selected topK value', async () => {
    mockNavigate.mockClear();
    renderHome();
    const input = screen.getByPlaceholderText(/search books, topics, passages/i);
    fireEvent.change(input, { target: { value: 'ethics' } });
    const submitBtn = screen.getByRole('button', { name: /^search$/i });
    await userEvent.click(submitBtn);
    expect(mockNavigate).toHaveBeenCalledWith('/results?q=ethics&k=5');
  });
});
