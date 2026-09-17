import React from 'react';

/**
 * Pill-shaped category or topic tag. Used in carousels, post footers
 * and service filter rows. Supports active/selected state.
 */
export function Tag({
  children,
  variant = 'outlined',
  active = false,
  onClick,
  icon,
  style: extraStyle = {},
}) {
  const base = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '5px',
    fontFamily: 'var(--font-body)',
    fontWeight: 'var(--font-weight-bold)',
    fontSize: '13px',
    borderRadius: 'var(--radius-full)',
    padding: '6px 16px',
    cursor: onClick ? 'pointer' : 'default',
    transition: 'var(--transition-fast)',
    whiteSpace: 'nowrap',
    userSelect: 'none',
    lineHeight: 1.2,
  };

  const variants = {
    outlined: {
      background: 'transparent',
      boxShadow: 'inset 0 0 0 1.5px var(--color-grey-300)',
      color: 'var(--color-text-body)',
    },
    'outlined-gold': {
      background: 'transparent',
      boxShadow: 'inset 0 0 0 1.5px var(--color-gold-500)',
      color: 'var(--color-gold-500)',
    },
    'outlined-white': {
      background: 'transparent',
      boxShadow: 'inset 0 0 0 1.5px rgba(255,255,255,0.5)',
      color: 'var(--color-white)',
    },
    filled: {
      background: 'var(--color-grey-100)',
      color: 'var(--color-text-body)',
    },
    'filled-gold': {
      background: 'var(--color-gold-100)',
      color: 'var(--color-gold-900)',
    },
    'filled-coral': {
      background: 'var(--color-coral-100)',
      color: 'var(--color-coral-700)',
    },
    'filled-sea': {
      background: 'var(--color-sea-100)',
      color: 'var(--color-sea-700)',
    },
    'filled-lime': {
      background: 'rgba(127,224,48,0.12)',
      color: 'var(--color-lime-500)',
    },
  };

  const activeOverride = active
    ? {
        background: 'var(--color-gold-100)',
        boxShadow: 'inset 0 0 0 1.5px var(--color-gold-500)',
        color: 'var(--color-gold-900)',
      }
    : {};

  return React.createElement(
    'span',
    {
      style: { ...base, ...variants[variant], ...activeOverride, ...extraStyle },
      onClick,
    },
    icon && React.createElement('span', {
      style: { display: 'flex', alignItems: 'center', flexShrink: 0 },
    }, icon),
    children,
  );
}
