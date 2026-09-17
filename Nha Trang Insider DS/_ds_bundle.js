/* @ds-bundle: {"format":3,"namespace":"NhaTrangInsiderDS_1c0e3d","components":[{"name":"Badge","sourcePath":"components/core/Badge.jsx"},{"name":"Button","sourcePath":"components/core/Button.jsx"},{"name":"Card","sourcePath":"components/core/Card.jsx"},{"name":"Tag","sourcePath":"components/core/Tag.jsx"}],"sourceHashes":{"components/core/Badge.jsx":"d92325f93d0e","components/core/Button.jsx":"b62ca36172d2","components/core/Card.jsx":"41948dab49a1","components/core/Tag.jsx":"bc6f5cbdd140"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.NhaTrangInsiderDS_1c0e3d = window.NhaTrangInsiderDS_1c0e3d || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/core/Badge.jsx
try { (() => {
/**
 * Compact label chip for service types, categories and status indicators.
 * Six colour variants cover every brand surface.
 */
function Badge({
  children,
  variant = 'gold',
  size = 'md',
  style: extraStyle = {}
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
    whiteSpace: 'nowrap'
  };
  const sizes = {
    sm: {
      padding: '4px 10px',
      fontSize: '9px'
    },
    md: {
      padding: '5px 13px',
      fontSize: '10px'
    },
    lg: {
      padding: '7px 18px',
      fontSize: '12px'
    }
  };
  const variants = {
    gold: {
      background: 'var(--gradient-gold)',
      color: 'var(--color-navy-900)',
      boxShadow: '0 2px 8px rgba(201,148,26,0.3)'
    },
    navy: {
      background: 'var(--color-navy-900)',
      color: 'var(--color-gold-300)',
      boxShadow: 'inset 0 0 0 1px var(--color-gold-500)'
    },
    coral: {
      background: 'var(--color-coral-500)',
      color: 'var(--color-white)',
      boxShadow: '0 2px 8px rgba(232,88,58,0.3)'
    },
    lime: {
      background: 'var(--color-lime-500)',
      color: 'var(--color-black)'
    },
    sea: {
      background: 'var(--color-sea-500)',
      color: 'var(--color-white)'
    },
    amber: {
      background: 'var(--color-amber-500)',
      color: 'var(--color-navy-900)'
    },
    outline: {
      background: 'transparent',
      color: 'var(--color-gold-500)',
      boxShadow: 'inset 0 0 0 1.5px var(--color-gold-500)'
    }
  };
  return React.createElement('span', {
    style: {
      ...base,
      ...sizes[size],
      ...variants[variant],
      ...extraStyle
    }
  }, children);
}
Object.assign(__ds_scope, { Badge });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Badge.jsx", error: String((e && e.message) || e) }); }

// components/core/Button.jsx
try { (() => {
/**
 * Primary interactive control. Five visual variants map to the
 * brand's four content modes plus a neutral ghost for dark overlays.
 */
function Button({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  fullWidth = false,
  onClick,
  icon,
  style: extraStyle = {}
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
    WebkitTapHighlightColor: 'transparent'
  };
  const sizes = {
    sm: {
      padding: '8px 20px',
      fontSize: '11px'
    },
    md: {
      padding: '12px 28px',
      fontSize: '13px'
    },
    lg: {
      padding: '15px 40px',
      fontSize: '14px'
    },
    xl: {
      padding: '18px 56px',
      fontSize: '15px'
    }
  };
  const variants = {
    primary: {
      background: 'var(--gradient-gold)',
      color: 'var(--color-navy-900)',
      boxShadow: 'var(--shadow-gold)'
    },
    secondary: {
      background: 'transparent',
      color: 'var(--color-gold-500)',
      border: '1.5px solid var(--color-gold-500)'
    },
    coral: {
      background: 'var(--color-coral-500)',
      color: 'var(--color-white)',
      boxShadow: 'var(--shadow-coral)'
    },
    ghost: {
      background: 'transparent',
      color: 'var(--color-white)',
      border: '1.5px solid rgba(255,255,255,0.45)'
    },
    dark: {
      background: 'var(--color-black)',
      color: 'var(--color-lime-500)',
      border: '1.5px solid var(--color-lime-500)',
      boxShadow: 'var(--shadow-lime)'
    }
  };
  return React.createElement('button', {
    style: {
      ...base,
      ...sizes[size],
      ...variants[variant],
      ...extraStyle
    },
    disabled,
    onClick
  }, icon && React.createElement('span', {
    style: {
      display: 'flex',
      alignItems: 'center',
      flexShrink: 0
    }
  }, icon), children);
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Button.jsx", error: String((e && e.message) || e) }); }

// components/core/Card.jsx
try { (() => {
/**
 * Flexible container card used in info layouts, service overviews
 * and Instagram carousel slide bodies.
 */
function Card({
  children,
  variant = 'white',
  padding = 'md',
  radius = 'lg',
  shadow = true,
  border,
  style: extraStyle = {}
}) {
  const variants = {
    white: {
      background: 'var(--color-white)',
      color: 'var(--color-text-body)'
    },
    cream: {
      background: 'var(--color-cream)',
      color: 'var(--color-text-body)'
    },
    navy: {
      background: 'var(--color-navy-900)',
      color: 'var(--color-white)'
    },
    dark: {
      background: 'var(--color-black)',
      color: 'var(--color-white)'
    },
    gold: {
      background: 'var(--gradient-gold)',
      color: 'var(--color-navy-900)'
    },
    coral: {
      background: 'var(--color-coral-500)',
      color: 'var(--color-white)'
    },
    sand: {
      background: 'var(--color-sand-100)',
      color: 'var(--color-text-body)'
    },
    sea: {
      background: 'var(--gradient-sea)',
      color: 'var(--color-white)'
    },
    'glass-navy': {
      background: 'var(--glass-navy)',
      backdropFilter: 'var(--blur-md)',
      WebkitBackdropFilter: 'var(--blur-md)',
      color: 'var(--color-white)'
    }
  };
  const paddings = {
    none: '0',
    sm: 'var(--space-4)',
    md: 'var(--space-6)',
    lg: 'var(--space-8)',
    xl: 'var(--space-12)'
  };
  const radii = {
    none: '0',
    sm: 'var(--radius-sm)',
    md: 'var(--radius-md)',
    lg: 'var(--radius-lg)',
    xl: 'var(--radius-xl)',
    '2xl': 'var(--radius-2xl)',
    full: 'var(--radius-full)'
  };
  const shadowMap = {
    white: 'var(--shadow-md)',
    cream: 'var(--shadow-sm)',
    navy: 'var(--shadow-navy)',
    dark: 'var(--shadow-xl)',
    gold: 'var(--shadow-gold)',
    coral: 'var(--shadow-coral)',
    sand: 'var(--shadow-sm)',
    sea: 'var(--shadow-lg)',
    'glass-navy': 'var(--shadow-lg)'
  };
  return React.createElement('div', {
    style: {
      ...variants[variant],
      padding: paddings[padding],
      borderRadius: radii[radius],
      boxShadow: shadow ? shadowMap[variant] || 'var(--shadow-md)' : 'none',
      border: border || 'none',
      overflow: 'hidden',
      ...extraStyle
    }
  }, children);
}
Object.assign(__ds_scope, { Card });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Card.jsx", error: String((e && e.message) || e) }); }

// components/core/Tag.jsx
try { (() => {
/**
 * Pill-shaped category or topic tag. Used in carousels, post footers
 * and service filter rows. Supports active/selected state.
 */
function Tag({
  children,
  variant = 'outlined',
  active = false,
  onClick,
  icon,
  style: extraStyle = {}
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
    lineHeight: 1.2
  };
  const variants = {
    outlined: {
      background: 'transparent',
      boxShadow: 'inset 0 0 0 1.5px var(--color-grey-300)',
      color: 'var(--color-text-body)'
    },
    'outlined-gold': {
      background: 'transparent',
      boxShadow: 'inset 0 0 0 1.5px var(--color-gold-500)',
      color: 'var(--color-gold-500)'
    },
    'outlined-white': {
      background: 'transparent',
      boxShadow: 'inset 0 0 0 1.5px rgba(255,255,255,0.5)',
      color: 'var(--color-white)'
    },
    filled: {
      background: 'var(--color-grey-100)',
      color: 'var(--color-text-body)'
    },
    'filled-gold': {
      background: 'var(--color-gold-100)',
      color: 'var(--color-gold-900)'
    },
    'filled-coral': {
      background: 'var(--color-coral-100)',
      color: 'var(--color-coral-700)'
    },
    'filled-sea': {
      background: 'var(--color-sea-100)',
      color: 'var(--color-sea-700)'
    },
    'filled-lime': {
      background: 'rgba(127,224,48,0.12)',
      color: 'var(--color-lime-500)'
    }
  };
  const activeOverride = active ? {
    background: 'var(--color-gold-100)',
    boxShadow: 'inset 0 0 0 1.5px var(--color-gold-500)',
    color: 'var(--color-gold-900)'
  } : {};
  return React.createElement('span', {
    style: {
      ...base,
      ...variants[variant],
      ...activeOverride,
      ...extraStyle
    },
    onClick
  }, icon && React.createElement('span', {
    style: {
      display: 'flex',
      alignItems: 'center',
      flexShrink: 0
    }
  }, icon), children);
}
Object.assign(__ds_scope, { Tag });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Tag.jsx", error: String((e && e.message) || e) }); }

__ds_ns.Badge = __ds_scope.Badge;

__ds_ns.Button = __ds_scope.Button;

__ds_ns.Card = __ds_scope.Card;

__ds_ns.Tag = __ds_scope.Tag;

})();
