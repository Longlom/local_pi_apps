/**
 * Card — flexible container for info sections, service cards, and carousel slide bodies.
 * Supports 9 visual variants matching every brand content mode.
 *
 * @example
 * <Card variant="navy" padding="lg">
 *   <h2>VIP Fast-Track</h2>
 * </Card>
 * <Card variant="glass-navy" radius="xl">Overlay content</Card>
 * <Card variant="gold" padding="sm">Highlight fact</Card>
 *
 * @variants
 * white · cream · navy · dark · gold · coral · sand · sea · glass-navy
 */
export interface CardProps {
  children: React.ReactNode;
  /** Background style. Default: white */
  variant?: 'white' | 'cream' | 'navy' | 'dark' | 'gold' | 'coral' | 'sand' | 'sea' | 'glass-navy';
  /** Padding scale. Default: md */
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  /** Corner radius. Default: lg */
  radius?: 'none' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
  /** Show box-shadow. Default: true */
  shadow?: boolean;
  /** Override border (e.g. "1.5px solid var(--color-gold-500)") */
  border?: string;
  style?: React.CSSProperties;
}
