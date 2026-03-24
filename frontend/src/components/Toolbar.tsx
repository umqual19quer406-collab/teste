type Props = {
  left?: React.ReactNode;
  right?: React.ReactNode;
};

export function Toolbar({ left, right }: Props) {
  return (
    <div className="toolbar">
      <div className="toolbar-left">{left}</div>
      <div className="toolbar-right">{right}</div>
    </div>
  );
}