import { useRef, useState, type ChangeEvent, type DragEvent } from 'react'
import { FileUp } from 'lucide-react'
import { cn } from '../../lib/cn'
import { EEGChart } from '../eeg/EEGChart'

interface UploadZoneProps {
  onFile: (file: File) => void
}

export function UploadZone({ onFile }: UploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [over, setOver] = useState(false)

  const handleFiles = (files: FileList | null) => {
    const file = files?.[0]
    if (file) onFile(file)
  }

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setOver(false)
    handleFiles(event.dataTransfer.files)
  }

  const onChange = (event: ChangeEvent<HTMLInputElement>) => {
    handleFiles(event.target.files)
    event.target.value = ''
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault()
        setOver(true)
      }}
      onDragLeave={() => setOver(false)}
      onDrop={onDrop}
      className={cn(
        'rounded-na border border-dashed px-6 py-10 text-center transition-colors',
        over ? 'border-accent bg-accent-soft' : 'border-border bg-card dark:bg-surface',
      )}
    >
      <div className="mx-auto mb-5 max-w-md opacity-80">
        <EEGChart channels={['FP1', 'FP2', 'C3', 'C4']} height={92} compact showTimeAxis={false} />
      </div>
      <p className="text-base font-semibold">Drop your EEG file here</p>
      <p className="mt-1 text-sm text-muted">EDF, BDF, SET, or CSV · demonstration upload only</p>
      <div className="mt-5">
        <input
          ref={inputRef}
          type="file"
          className="sr-only"
          accept=".edf,.bdf,.set,.csv,.txt"
          onChange={onChange}
        />
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="inline-flex items-center gap-2 rounded-na border border-border px-4 py-2 text-sm font-semibold text-foreground transition-colors hover:bg-accent-soft"
        >
          <FileUp size={16} aria-hidden />
          Browse Files
        </button>
      </div>
    </div>
  )
}
