type HeroMetric = {
  label: string;
  value: string;
};

type Props = {
  icon: string;
  eyebrow: string;
  title: string;
  description: string;
  metrics?: HeroMetric[];
  actions?: React.ReactNode;
  backgroundImage?: string;
  backgroundPosition?: string;
  backgroundSize?: string;
};

export function PageHero({
  icon,
  eyebrow,
  title,
  description,
  metrics = [],
  actions,
  backgroundImage,
  backgroundPosition,
  backgroundSize,
}: Props) {
  return (
    <section
      className={`hero-panel ${backgroundImage ? "hero-panel-bg" : ""}`.trim()}
      style={
        backgroundImage
          ? ({
              ["--hero-bg" as string]: `url("${backgroundImage}")`,
              ["--hero-bg-position" as string]: backgroundPosition ?? "center",
              ["--hero-bg-size" as string]: backgroundSize ?? "cover",
            } as React.CSSProperties)
          : undefined
      }
    >
      <div className="hero-main">
        <div className="hero-icon-wrap">
          <img src={icon} alt="" className="hero-icon" />
        </div>

        <div className="hero-copy">
          <div className="hero-eyebrow">{eyebrow}</div>
          <h1 className="hero-title">{title}</h1>
          <p className="hero-description">{description}</p>

          {metrics.length > 0 ? (
            <div className="hero-metrics">
              {metrics.map((metric) => (
                <div key={metric.label} className="hero-metric">
                  <div className="hero-metric-label">{metric.label}</div>
                  <div className="hero-metric-value">{metric.value}</div>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      </div>

      {actions ? <div className="hero-actions">{actions}</div> : null}
    </section>
  );
}
