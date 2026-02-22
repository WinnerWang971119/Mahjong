import { useGameStore } from '../../store/gameStore'

interface SettingsPanelProps {
  onBack: () => void
}

export default function SettingsPanel({ onBack }: SettingsPanelProps) {
  const settings = useGameStore((s) => s.settings)
  const updateSettings = useGameStore((s) => s.updateSettings)

  return (
    <div className="min-h-screen bg-table-green flex flex-col items-center justify-center">
      <div className="bg-honor-dark rounded-xl p-8 max-w-md w-full text-white">
        <h2 className="text-2xl font-bold mb-6">設定 (Settings)</h2>

        {/* Animation Speed */}
        <div className="mb-4">
          <label className="block text-sm text-white/60 mb-1">動畫速度 (Animation Speed)</label>
          <select
            value={settings.animationSpeed}
            onChange={(e) => updateSettings({ animationSpeed: e.target.value as 'slow' | 'normal' | 'fast' | 'instant' })}
            className="w-full bg-white/10 border border-white/20 rounded px-3 py-2 text-white"
          >
            <option value="slow">慢 (Slow)</option>
            <option value="normal">正常 (Normal)</option>
            <option value="fast">快 (Fast)</option>
            <option value="instant">即時 (Instant)</option>
          </select>
        </div>

        {/* Language */}
        <div className="mb-4">
          <label className="block text-sm text-white/60 mb-1">語言 (Language)</label>
          <select
            value={settings.language}
            onChange={(e) => updateSettings({ language: e.target.value as 'zh-TW' | 'en' })}
            className="w-full bg-white/10 border border-white/20 rounded px-3 py-2 text-white"
          >
            <option value="zh-TW">繁體中文</option>
            <option value="en">English</option>
          </select>
        </div>

        {/* Table Background */}
        <div className="mb-4">
          <label className="block text-sm text-white/60 mb-1">桌面背景 (Table Background)</label>
          <div className="flex gap-2">
            {(['green', 'blue', 'wood'] as const).map((bg) => (
              <button
                key={bg}
                onClick={() => updateSettings({ tableBackground: bg })}
                className={`px-4 py-2 rounded border ${settings.tableBackground === bg ? 'border-yellow-400 bg-white/20' : 'border-white/20'}`}
              >
                {bg === 'green' ? '綠' : bg === 'blue' ? '藍' : '木'}
              </button>
            ))}
          </div>
        </div>

        {/* Sound */}
        <div className="mb-6">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={settings.soundEnabled}
              onChange={(e) => updateSettings({ soundEnabled: e.target.checked })}
              className="w-4 h-4"
            />
            <span>音效 (Sound Effects)</span>
          </label>
        </div>

        <button
          onClick={onBack}
          className="w-full py-2 bg-white/20 hover:bg-white/30 rounded-lg font-bold transition-colors"
        >
          返回 (Back)
        </button>
      </div>
    </div>
  )
}
