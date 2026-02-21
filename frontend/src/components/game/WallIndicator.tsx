interface WallIndicatorProps {
  remaining: number
}

export default function WallIndicator({ remaining }: WallIndicatorProps) {
  return (
    <div className="flex items-center justify-center bg-black/30 text-white rounded-full w-12 h-12 text-sm font-bold">
      {remaining}
    </div>
  )
}
