import React from 'react';

/**
 * Compact label chip for service types, categories and status indicators.
 * Six colour variants cover every brand surface.
 */
export function Badge({
  children,
  variant = 'gold',
  size = 'md',
  style: extraStyle = {},
}) {
  const base = {
    display: 'inline-flex',
    alignItems: 'center',
    fontFamily: 'var(--font-display)',
    fontWeight: 'var(--font-weight-extrabold)',
    letterSpacing: 'var(--letter-spacing-wider)',
    textTransform: 'uppercase',
    borderRadius: 'var(--radius-full)',
    lineHeight: 1,
    whiteSpace: 'nowrap',
  };

  const sizes = {
    sm: { padding: '4px 10px',  fontSize: '9px'  },
    md: { padding: '5px 13px',  fontSize: '10px' },
    lg: { padding: '7px 18px',  fontSize: '12px' },
  };

  const variants = {
    gold: {
      background: 'var(--gradient-gold)',
      color: 'var(--color-navy-900)',
      boxShadow: '0 2px 8px rgba(201,148,26,0.3)',
    },
    navy: {
      background: 'var(--color-navy-900)',
      color: 'var(--color-gold-300)',
      boxShadow: 'inset 0 0 0 1px var(--color-gold-500)',
    },
    coral: {
      background: 'var(--color-coral-500)',
      color: 'var(--color-white)',
      boxShadow: '0 2px 8px rgba(232,88,58,0.3)',
    },
    lime: {
      background: 'var(--color-lime-500)',
      color: 'var(--color-black)',
    },
    sea: {
      background: 'var(--color-sea-500)',
      color: 'var(--color-white)',
    },
    amber: {
      background: 'var(--color-amber-500)',
      color: 'var(--color-navy-900)',
    },
    outline: {
      background: 'transparent',
      color: 'var(--color-gold-500)',
      boxShadow: 'inset 0 0 0 1.5px var(--color-gold-500)',
    },
  };

  return React.createElement(
    'span',
    { style: { ...base, ...sizes[size], ...variants[variant], ...extraStyle } },
    children,
  );
}
