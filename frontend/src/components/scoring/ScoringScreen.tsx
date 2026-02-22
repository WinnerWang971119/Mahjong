import type { ScoringBreakdown } from '../../types/game'
import Tile from '../tiles/Tile'

interface ScoringScreenProps {
  scoring: ScoringBreakdown | null
  winningHand?: string[]
  onContinue: () => void
}

const WIND_LABELS = ['\u6771', '\u5357', '\u897F', '\u5317']

export default function ScoringScreen({ scoring, winningHand, onContinue }: ScoringScreenProps) {
  return (
    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center">
      <div className="bg-honor-dark rounded-xl p-8 max-w-lg w-full text-white">
        <h2 className="text-3xl font-bold text-center mb-6 text-yellow-400">{'\u8A08\u53F0\u660E\u7D30'}</h2>

        {/* Winning hand display */}
        {winningHand && winningHand.length > 0 && (
          <div className="flex gap-1 justify-center mb-6 flex-wrap">
            {winningHand.map((tile, i) => (
              <Tile key={i} code={tile} />
            ))}
          </div>
        )}

        {scoring ? (
          <>
            {/* Yaku list */}
            <div className="mb-6">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/20">
                    <th className="text-left py-1">{'\u53F0\u540D'}</th>
                    <th className="text-right py-1">{'\u53F0\u6578'}</th>
                  </tr>
                </thead>
                <tbody>
                  {scoring.yaku.map(([name, tai], i) => (
                    <tr key={i} className="border-b border-white/10">
                      <td className="py-1">{name}</td>
                      <td className="text-right py-1 text-yellow-400">{tai}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Totals */}
            <div className="flex justify-between items-center mb-4 text-lg font-bold">
              <span>{'\u7E3D\u8A08'}</span>
              <span className="text-yellow-400">
                {scoring.subtotal !== scoring.total
                  ? `${scoring.subtotal} \u2192 ${scoring.total} (\u4E0A\u965081\u53F0)`
                  : `${scoring.total} \u53F0`}
              </span>
            </div>

            {/* Payment breakdown */}
            <div className="mb-6">
              <h3 className="text-sm text-white/60 mb-2">{'\u6536\u652F\u660E\u7D30'}</h3>
              {Object.entries(scoring.payments).map(([seat, amount]) => (
                <div key={seat} className="flex justify-between text-sm">
                  <span>{WIND_LABELS[Number(seat)]}{'\u5BB6'}</span>
                  <span className={Number(amount) < 0 ? 'text-green-400' : 'text-red-400'}>
                    {Number(amount) < 0 ? `+${Math.abs(Number(amount))}` : `-${amount}`}
                  </span>
                </div>
              ))}
            </div>
          </>
        ) : (
          <p className="text-center text-white/60 mb-6">{'\u6D41\u5C40 \u2014 \u7121\u4EBA\u80E1\u724C'}</p>
        )}

        <button
          onClick={onContinue}
          className="w-full py-3 bg-yellow-500 hover:bg-yellow-600 text-honor-dark font-bold rounded-lg text-lg transition-colors"
        >
          {'\u7E7C\u7E8C'} (Continue)
        </button>
      </div>
    </div>
  )
}
