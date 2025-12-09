'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Card, CardContent } from '@/components/ui/card'
import { Slider } from '@/components/ui/slider'
import { Upload, X, Image as ImageIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils/cn'

interface FaceReferenceUploadProps {
  value: string | null
  onChange: (value: string | null) => void
  faceStrength: number
  onFaceStrengthChange: (value: number) => void
}

export function FaceReferenceUpload({
  value,
  onChange,
  faceStrength,
  onFaceStrengthChange,
}: FaceReferenceUploadProps) {
  const [preview, setPreview] = useState<string | null>(value)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = () => {
        const result = reader.result as string
        setPreview(result)
        onChange(result)
      }
      reader.readAsDataURL(file)
    }
  }, [onChange])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.webp'],
    },
    maxFiles: 1,
  })

  const handleRemove = () => {
    setPreview(null)
    onChange(null)
  }

  if (preview) {
    return (
      <div className="space-y-4">
        <div className="relative">
          <div className="relative aspect-square w-full overflow-hidden rounded-lg border">
            <img
              src={preview}
              alt="Face reference"
              className="h-full w-full object-cover"
            />
          </div>
          <Button
            variant="destructive"
            size="icon"
            className="absolute top-2 right-2"
            onClick={handleRemove}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">
            Face Strength: {faceStrength.toFixed(2)}
          </label>
          <Slider
            value={[faceStrength]}
            onValueChange={(values) => onFaceStrengthChange(values[0])}
            min={0}
            max={1}
            step={0.05}
          />
          <p className="text-xs text-muted-foreground">
            Higher values make the face more prominent, lower values blend it more naturally
          </p>
        </div>
      </div>
    )
  }

  return (
    <div
      {...getRootProps()}
      className={cn(
        'cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition-colors',
        isDragActive
          ? 'border-primary bg-primary/5'
          : 'border-muted-foreground/25 hover:border-primary/50'
      )}
    >
      <input {...getInputProps()} />
      <div className="flex flex-col items-center justify-center space-y-4">
        <div className="rounded-full bg-muted p-4">
          <Upload className="h-6 w-6 text-muted-foreground" />
        </div>
        <div>
          <p className="text-sm font-medium">
            {isDragActive ? 'Drop image here' : 'Upload face reference'}
          </p>
          <p className="text-xs text-muted-foreground">
            Drag and drop or click to select
          </p>
        </div>
      </div>
    </div>
  )
}
