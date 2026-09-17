import React from 'react';

/**
 * Flexible container card used in info layouts, service overviews
 * and Instagram carousel slide bodies.
 */
export function Card({
  children,
  variant = 'white',
  padding = 'md',
  radius = 'lg',
  shadow = true,
  border,
  style: extraStyle = {},
}) {
  const variants = {
    white:      { background: 'var(--color-white)',        color: 'var(--color-text-body)' },
    cream:      { background: 'var(--color-cream)',        color: 'var(--color-text-body)' },
    navy:       { background: 'var(--color-navy-900)',     color: 'var(--color-white)' },
    dark:       { background: 'var(--color-black)',        color: 'var(--color-white)' },
    gold:       { background: 'var(--gradient-gold)',      color: 'var(--color-navy-900)' },
    coral:      { background: 'var(--color-coral-500)',    color: 'var(--color-white)' },
    sand:       { background: 'var(--color-sand-100)',     color: 'var(--color-text-body)' },
    sea:        { background: 'var(--gradient-sea)',       color: 'var(--color-white)' },
    'glass-navy': {
      background: 'var(--glass-navy)',
      backdropFilter: 'var(--blur-md)',
      WebkitBackdropFilter: 'var(--blur-md)',
      color: 'var(--color-white)',
    },
  };

  const paddings = {
    none: '0',
    sm:   'var(--space-4)',
    md:   'var(--space-6)',
    lg:   'var(--space-8)',
    xl:   'var(--space-12)',
  };

  const radii = {
    none:  '0',
    sm:    'var(--radius-sm)',
    md:    'var(--radius-md)',
    lg:    'var(--radius-lg)',
    xl:    'var(--radius-xl)',
    '2xl': 'var(--radius-2xl)',
    full:  'var(--radius-full)',
  };

  const shadowMap = {
    white: 'var(--shadow-md)',
    cream: 'var(--shadow-sm)',
    navy:  'var(--shadow-navy)',
    dark:  'var(--shadow-xl)',
    gold:  'var(--shadow-gold)',
    coral: 'var(--shadow-coral)',
    sand:  'var(--shadow-sm)',
    sea:   'var(--shadow-lg)',
    'glass-navy': 'var(--shadow-lg)',
  };

  return React.createElement(
    'div',
    {
      style: {
        ...variants[variant],
        padding: paddings[padding],
        borderRadius: radii[radius],
        boxShadow: shadow ? (shadowMap[variant] || 'var(--shadow-md)') : 'none',
        border: border || 'none',
        overflow: 'hidden',
        ...extraStyle,
      },
    },
    children,
  );
}
