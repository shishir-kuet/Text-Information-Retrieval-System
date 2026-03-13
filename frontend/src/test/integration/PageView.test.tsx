import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import React from 'react';
import PageView, { PageData } from '../../pages/PageView';

// ── mocks ──────────────────────────────────────────────────────────────────

const mockNavigate = vi.fn();

vi.mock('react-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router')>();
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock('motion/react', () => ({
  motion: new Proxy({} as Record<string, unknown>, {
    get: (_target, tag: string) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return ({ children, initial: _i, animate: _a, transition: _t, ...rest }: any) =>
        React.createElement(tag, rest, children);
    },
  }),
}));

const MOCK_PAGE: PageData = {
  page_id: 'ir_book_page_45',
  text_content: 'An inverted index is a data structure that maps terms to the documents they appear in. Information retrieval systems rely on efficient index construction and query processing.',
  display_page_number: '45',
  book_title: 'Introduction to Information Retrieval',
  author: 'Manning, Raghavan & Schütze',
  year: '2008',
  domain: 'Computer Science',
  page_number: 45,
  prev_page_id: 'ir_book_page_44',
  next_page_id: 'ir_book_page_46',
};

const mockFetch = (data = MOCK_PAGE, ok = true) => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok,
    status: ok ? 200 : 404,
    json: () => Promise.resolve(ok ? data : { error: 'Page not found' }),
  }));
};

// Render with route params and optional search query
const renderPageView = (pageId = 'ir_book_page_45', query = 'information retrieval') =>
  render(
    <MemoryRouter initialEntries={[`/page/${pageId}?q=${encodeURIComponent(query)}`]}>
      <PageView />
    </MemoryRouter>
  );

// We need to mock useParams so the component gets the right pageId
vi.mock('react-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router')>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ pageId: 'ir_book_page_45' }),
  };
});

// ── layout / header ─────────────────────────────────────────────────────────

describe('PageView — layout', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    mockFetch();
  });
  afterEach(() => vi.unstubAllGlobals());

  it('renders the book title in the header', async () => {
    renderPageView();
    await waitFor(() => expect(screen.getByText('Introduction to Information Retrieval')).toBeInTheDocument());
  });

  it('renders the page number badge', async () => {
    renderPageView();
    await waitFor(() => expect(screen.getByText(/Page 45/i)).toBeInTheDocument());
  });

  it('renders the author name', async () => {
    renderPageView();
    await waitFor(() => expect(screen.getByText(/Manning/i)).toBeInTheDocument());
  });

  it('renders the publication year', async () => {
    renderPageView();
    await waitFor(() => expect(screen.getByText('2008')).toBeInTheDocument());
  });

  it('renders the Back to Results button', async () => {
    renderPageView();
    await waitFor(() => expect(screen.getByRole('button', { name: /back to results/i })).toBeInTheDocument());
  });
});

// ── loading ──────────────────────────────────────────────────────────────────

describe('PageView — loading state', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('shows loading indicator initially', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})));
    renderPageView();
    expect(screen.getByText(/loading page/i)).toBeInTheDocument();
  });
});

// ── content ──────────────────────────────────────────────────────────────────

describe('PageView — page content', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    mockFetch();
  });
  afterEach(() => vi.unstubAllGlobals());

  it('renders the page text content', async () => {
    renderPageView();
    await waitFor(() => expect(screen.getByText(/inverted index is a data structure/i)).toBeInTheDocument());
  });

  it('shows highlighted terms bar when query is provided', async () => {
    renderPageView();
    await waitFor(() => expect(screen.getByText(/highlighted terms/i)).toBeInTheDocument());
  });

  it('shows individual highlighted term pills', async () => {
    renderPageView('ir_book_page_45', 'information retrieval');
    await waitFor(() => {
      // The term pills appear in the highlighted-terms bar (as span elements with orange bg)
      // Use getAllByText since term may also appear highlighted in page text
      expect(screen.getAllByText('information').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('retrieval').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('does not show highlighted terms bar when query is empty', async () => {
    renderPageView('ir_book_page_45', '');
    await waitFor(() => {
      expect(screen.queryByText(/highlighted terms/i)).not.toBeInTheDocument();
    });
  });
});

// ── navigation ──────────────────────────────────────────────────────────────

describe('PageView — navigation', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    mockFetch();
  });
  afterEach(() => vi.unstubAllGlobals());

  it('renders the Previous Page button', async () => {
    renderPageView();
    await waitFor(() => expect(screen.getByRole('button', { name: /previous page/i })).toBeInTheDocument());
  });

  it('renders the Next Page button', async () => {
    renderPageView();
    await waitFor(() => expect(screen.getByRole('button', { name: /next page/i })).toBeInTheDocument());
  });

  it('Previous Page button is enabled when prev_page_id exists', async () => {
    renderPageView();
    await waitFor(() => {
      const btn = screen.getByRole('button', { name: /previous page/i });
      expect(btn).not.toBeDisabled();
    });
  });

  it('Next Page button is enabled when next_page_id exists', async () => {
    renderPageView();
    await waitFor(() => {
      const btn = screen.getByRole('button', { name: /next page/i });
      expect(btn).not.toBeDisabled();
    });
  });

  it('Previous Page button is disabled when no prev_page_id', async () => {
    mockFetch({ ...MOCK_PAGE, prev_page_id: null });
    renderPageView();
    await waitFor(() => {
      const btn = screen.getByRole('button', { name: /previous page/i });
      expect(btn).toBeDisabled();
    });
  });

  it('Next Page button is disabled when no next_page_id', async () => {
    mockFetch({ ...MOCK_PAGE, next_page_id: null });
    renderPageView();
    await waitFor(() => {
      const btn = screen.getByRole('button', { name: /next page/i });
      expect(btn).toBeDisabled();
    });
  });

  it('clicking Next Page navigates to next page with query', async () => {
    renderPageView();
    await waitFor(() => screen.getByRole('button', { name: /next page/i }));
    fireEvent.click(screen.getByRole('button', { name: /next page/i }));
    expect(mockNavigate).toHaveBeenCalledWith(
      expect.stringContaining('ir_book_page_46')
    );
  });

  it('clicking Previous Page navigates to previous page with query', async () => {
    renderPageView();
    await waitFor(() => screen.getByRole('button', { name: /previous page/i }));
    fireEvent.click(screen.getByRole('button', { name: /previous page/i }));
    expect(mockNavigate).toHaveBeenCalledWith(
      expect.stringContaining('ir_book_page_44')
    );
  });

  it('Back to Results navigates to /results with the same query', async () => {
    renderPageView('ir_book_page_45', 'information retrieval');
    await waitFor(() => screen.getByRole('button', { name: /back to results/i }));
    fireEvent.click(screen.getByRole('button', { name: /back to results/i }));
    expect(mockNavigate).toHaveBeenCalledWith(
      expect.stringContaining('/results')
    );
  });
});

// ── error ──────────────────────────────────────────────────────────────────

describe('PageView — error state', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('shows error state on non-ok response', async () => {
    mockFetch(MOCK_PAGE, false);
    renderPageView();
    await waitFor(() => expect(screen.getByText(/page not found/i)).toBeInTheDocument());
  });

  it('shows error state on fetch rejection', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Network Error')));
    renderPageView();
    await waitFor(() => expect(screen.getByText(/page not found/i)).toBeInTheDocument());
  });
});
