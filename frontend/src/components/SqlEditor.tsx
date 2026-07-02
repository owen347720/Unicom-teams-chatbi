import { Input } from 'antd';

interface SqlEditorProps {
  value: string;
  onChange: (value: string) => void;
}

export function SqlEditor({ value, onChange }: SqlEditorProps) {
  return (
    <label className="field-block">
      <span>SQL</span>
      <Input.TextArea
        rows={7}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="生成的 SQL 会显示在这里，可在执行前修改"
      />
    </label>
  );
}
