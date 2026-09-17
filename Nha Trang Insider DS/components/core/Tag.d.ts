/**
 * Tag — pill-shaped category or topic filter tag.
 * Use in carousel footers, service filter rows and post topic labels.
 *
 * @example
 * <Tag variant="filled-gold" active>VIP Трансфер</Tag>
 * <Tag variant="outlined">Острова</Tag>
 * <Tag variant="filled-coral" onClick={handleClick}>Fast-Track</Tag>
 * <Tag variant="outlined-white">Камрань</Tag>
 *
 * @variants
 * outlined · outlined-gold · outlined-white ·
 * filled · filled-gold · filled-coral · filled-sea · filled-lime
 */
export interface TagProps {
  children: React.ReactNode;
  /** Visual variant. Default: outlined */
  variant?:
    | 'outlined'
    | 'outlined-gold'
    | 'outlined-white'
    | 'filled'
    | 'filled-gold'
    | 'filled-coral'
    | 'filled-sea'
    | 'filled-lime';
  /** Highlighted/selected state — forces gold active style */
  active?: boolean;
  onClick?: () => void;
  /** Leading icon element */
  icon?: React.ReactNode;
  style?: React.CSSProperties;
}
