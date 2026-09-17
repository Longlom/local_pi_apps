import React from 'react';

/**
 * Primary interactive control. Five visual variants map to the
 * brand's four content modes plus a neutral ghost for dark overlays.
 */
export function Button({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  fullWidth = false,
  onClick,
  icon,
  style: extraStyle = {},
}) {
  const base = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    fontFamily: 'var(--font-display)',
    fontWeight: 'var(--font-weight-bold)',
    letterSpacing: 'var(--letter-spacing-wide)',
    textTransform: 'uppercase',
    border: 'none',
    borderRadius: 'var(--radius-full)',
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.48 : 1,
    transition: 'var(--transition-normal)',
    whiteSpace: 'nowrap',
    textDecoration: 'none',
    width: fullWidth ? '100%' : 'auto',
    userSelect: 'none',
    outline: 'none',
    WebkitTapHighlightColor: 'transparent',
  };

  const sizes = {
    sm: { padding: '8px 20px',  fontSize: '11px' },
    md: { padding: '12px 28px', fontSize: '13px' },
    lg: { padding: '15px 40px', fontSize: '14px' },
    xl: { padding: '18px 56px', fontSize: '15px' },
  };

  const variants = {
    primary: {
      background: 'var(--gradient-gold)',
      color: 'var(--color-navy-900)',
      boxShadow: 'var(--shadow-gold)',
    },
    secondary: {
      background: 'transparent',
      color: 'var(--color-gold-500)',
      border: '1.5px solid var(--color-gold-500)',
    },
    coral: {
      background: 'var(--color-coral-500)',
      color: 'var(--color-white)',
      boxShadow: 'var(--shadow-coral)',
    },
    ghost: {
      background: 'transparent',
      color: 'var(--color-white)',
      border: '1.5px solid rgba(255,255,255,0.45)',
    },
    dark: {
      background: 'var(--color-black)',
      color: 'var(--color-lime-500)',
      border: '1.5px solid var(--color-lime-500)',
      boxShadow: 'var(--shadow-lime)',
    },
  };

  return React.createElement(
    'button',
    {
      style: { ...base, ...sizes[size], ...variants[variant], ...extraStyle },
      disabled,
      onClick,
    },
    icon && React.createElement('span', {
      style: { display: 'flex', alignItems: 'center', flexShrink: 0 },
    }, icon),
    children,
  );
}
