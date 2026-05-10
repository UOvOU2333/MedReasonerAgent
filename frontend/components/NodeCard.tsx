import { Brain, CheckCircle2, Clock3 } from "lucide-react";

type Props = {
  data: {
    label: string;
    active?: boolean;
    complete?: boolean;
  };
};

export default function NodeCard({ data }: Props) {
  const status = data.complete ? "complete" : data.active ? "active" : "idle";
  return (
    <div className={`node-card ${status}`}>
      {data.complete ? <CheckCircle2 size={18} /> : data.active ? <Clock3 size={18} /> : <Brain size={18} />}
      <span>{data.label}</span>
    </div>
  );
}
