/**
 * Button — primary interactive control for Nha Trang Insider brand.
 * Use for CTAs in Instagram stories, carousel end-slides, and web CTAs.
 *
 * @example
 * <Button variant="primary" size="lg">Заказать Fast-Track</Button>
 * <Button variant="coral" size="md" icon={<ArrowIcon />}>Подробнее</Button>
 * <Button variant="dark" size="md">Узнать цену</Button>
 *
 * @variants
 * - primary  — gold metallic gradient on navy text; main CTA
 * - secondary — transparent with gold border; secondary action
 * - coral    — warm coral fill; sunset / warm-direction CTA
 * - ghost    — white outline on dark/photo backgrounds
 * - dark     — black fill with lime border; viral dark-mode slides
 *
 * @sizes sm · md (default) · lg · xl
 */
export interface ButtonProps {
  children: React.ReactNode;
  /** Visual style. Default: primary */
  variant?: 'primary' | 'secondary' | 'coral' | 'ghost' | 'dark';
  /** Height + padding scale. Default: md */
  size?: 'sm' | 'md' | 'lg' | 'xl';
  disabled?: boolean;
  /** Stretch to full container width */
  fullWidth?: boolean;
  onClick?: () => void;
  /** Leading icon element */
  icon?: React.ReactNode;
  style?: React.CSSProperties;
}
