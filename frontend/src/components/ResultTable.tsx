import type { ExecuteSqlResponse } from '../types';

interface ResultTableProps {
  result: ExecuteSqlResponse | null;
}

export function ResultTable({ result }: ResultTableProps) {
  if (!result) {
    return <div className="empty-state compact">暂无查询结果</div>;
  }

  return (
    <div className="result-block">
      <div className="result-summary">
        {result.row_count} 行 · {result.execution_time.toFixed(2)} 秒
      </div>
      <div className="table-scroll">
        <table className="result-table">
          <thead>
            <tr>
              {result.columns.map((column) => (
                <th key={column}>{column}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {result.rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.map((value, columnIndex) => (
                  <td key={`${rowIndex}-${columnIndex}`}>{String(value)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
