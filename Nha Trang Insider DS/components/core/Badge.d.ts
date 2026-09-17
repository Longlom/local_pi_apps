/**
 * Badge — compact label chip for service types, categories and content mode indicators.
 * Use in post headers, carousel slides and service grids.
 *
 * @example
 * <Badge variant="gold">VIP</Badge>
 * <Badge variant="coral" size="lg">Fast-Track</Badge>
 * <Badge variant="lime">Инсайдер</Badge>
 * <Badge variant="navy">Камрань</Badge>
 *
 * @variants
 * - gold    — metallic gradient; premium brand default
 * - navy    — dark with gold text and border
 * - coral   — warm coral; sunset direction
 * - lime    — bright lime on black; viral style
 * - sea     — teal; ocean/beach content
 * - amber   — yellow; tropical/info posts
 * - outline — transparent gold border only
 */
export interface BadgeProps {
  children: React.ReactNode;
  /** Colour variant. Default: gold */
  variant?: 'gold' | 'navy' | 'coral' | 'lime' | 'sea' | 'amber' | 'outline';
  /** Size scale. Default: md */
  size?: 'sm' | 'md' | 'lg';
  style?: React.CSSProperties;
}
