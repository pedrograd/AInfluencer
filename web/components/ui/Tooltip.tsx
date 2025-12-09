'use client'

import React, { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import ReactDOM from 'react-dom'

import { cn } from '@/lib/utils/cn'

type TooltipContextValue = {
  open: boolean
  setOpen: (open: boolean) => void
  delayDuration: number
  triggerRef: React.MutableRefObject<HTMLElement | null>
}

const TooltipContext = React.createContext<TooltipContextValue | null>(null)

const TooltipProvider: React.FC<React.PropsWithChildren> = ({ children }) => <>{children}</>

type TooltipProps = React.PropsWithChildren<{
  delayDuration?: number
  defaultOpen?: boolean
  open?: boolean
  onOpenChange?: (open: boolean) => void
}>

const Tooltip: React.FC<TooltipProps> = ({
  children,
  delayDuration = 0,
  defaultOpen = false,
  open,
  onOpenChange,
}) => {
  const [internalOpen, setInternalOpen] = useState(defaultOpen)
  const isControlled = open !== undefined
  const resolvedOpen = isControlled ? Boolean(open) : internalOpen
  const triggerRef = useRef<HTMLElement | null>(null)

  const setOpen = (next: boolean) => {
    if (!isControlled) setInternalOpen(next)
    onOpenChange?.(next)
  }

  const value = useMemo<TooltipContextValue>(
    () => ({
      open: resolvedOpen,
      setOpen,
      delayDuration,
      triggerRef,
    }),
    [resolvedOpen, delayDuration]
  )

  return <TooltipContext.Provider value={value}>{children}</TooltipContext.Provider>
}

const useTooltipContext = () => {
  const ctx = React.useContext(TooltipContext)
  if (!ctx) throw new Error('Tooltip components must be used within <Tooltip>')
  return ctx
}

type EventHandler<T extends React.SyntheticEvent = React.SyntheticEvent> =
  | ((event: T) => void)
  | (() => void)
  | undefined

const composeHandlers = <T extends React.SyntheticEvent>(
  theirs?: EventHandler<T>,
  ours?: EventHandler<T>
) => {
  return (event: T) => {
    theirs?.(event)
    if (!event.defaultPrevented) {
      (ours as any)?.(event)
    }
  }
}

type TriggerProps = React.HTMLAttributes<HTMLElement> & { asChild?: boolean }

const TooltipTrigger = React.forwardRef<HTMLElement, TriggerProps>(
  ({ asChild = false, onMouseEnter, onMouseLeave, onFocus, onBlur, children, ...props }, ref) => {
    const { setOpen, delayDuration, triggerRef } = useTooltipContext()
    const timerRef = useRef<NodeJS.Timeout | null>(null)

    const handleOpen = () => {
      if (delayDuration > 0) {
        if (timerRef.current) clearTimeout(timerRef.current)
        timerRef.current = setTimeout(() => setOpen(true), delayDuration)
      } else {
        setOpen(true)
      }
    }

    const handleClose = () => {
      if (timerRef.current) clearTimeout(timerRef.current)
      setOpen(false)
    }

    const attachRef = (node: HTMLElement | null) => {
      triggerRef.current = node
      if (typeof ref === 'function') {
        ref(node)
      } else if (ref) {
        ;(ref as React.MutableRefObject<HTMLElement | null>).current = node
      }
      const childRef = (children as any)?.ref
      if (typeof childRef === 'function') {
        childRef(node)
      } else if (childRef) {
        childRef.current = node
      }
    }

    const eventProps = {
      onMouseEnter: composeHandlers(onMouseEnter, handleOpen),
      onMouseLeave: composeHandlers(onMouseLeave, handleClose),
      onFocus: composeHandlers(onFocus, handleOpen),
      onBlur: composeHandlers(onBlur, handleClose),
    }

    if (asChild && React.isValidElement(children)) {
      return React.cloneElement(children, {
        ...props,
        ...eventProps,
        ref: attachRef,
      })
    }

    return (
      <span {...props} {...eventProps} ref={attachRef}>
        {children}
      </span>
    )
  }
)
TooltipTrigger.displayName = 'TooltipTrigger'

type TooltipContentProps = React.HTMLAttributes<HTMLDivElement> & {
  side?: 'top' | 'bottom' | 'left' | 'right'
  sideOffset?: number
}

const TooltipContent = React.forwardRef<HTMLDivElement, TooltipContentProps>(
  ({ className, side = 'top', sideOffset = 4, style, ...props }, ref) => {
    const { open, triggerRef } = useTooltipContext()
    const [coords, setCoords] = useState<{ top: number; left: number }>({ top: 0, left: 0 })

    useLayoutEffect(() => {
      if (!open) return
      const trigger = triggerRef.current
      if (!trigger || typeof window === 'undefined') return
      const rect = trigger.getBoundingClientRect()
      const left = rect.left + rect.width / 2 + window.scrollX
      let top = rect.top + window.scrollY
      if (side === 'top') {
        top -= sideOffset
      } else if (side === 'bottom') {
        top += rect.height + sideOffset
      } else if (side === 'left' || side === 'right') {
        top += rect.height / 2 + window.scrollY
      }
      setCoords({ top, left })
    }, [open, side, sideOffset, triggerRef])

    useEffect(() => {
      if (!open) return
      const handleScroll = () => setCoords((coords) => ({ ...coords }))
      window.addEventListener('scroll', handleScroll, true)
      window.addEventListener('resize', handleScroll, true)
      return () => {
        window.removeEventListener('scroll', handleScroll, true)
        window.removeEventListener('resize', handleScroll, true)
      }
    }, [open])

    if (!open || typeof document === 'undefined') return null

    const computeTransform = () => {
      if (side === 'top') return 'translate(-50%, -100%)'
      if (side === 'bottom') return 'translate(-50%, 0)'
      if (side === 'left') return 'translate(-100%, -50%)'
      return 'translate(0, -50%)'
    }

    const content = (
      <div
        ref={ref}
        role="tooltip"
        style={{
          position: 'absolute',
          top: coords.top,
          left: coords.left,
          transform: computeTransform(),
          ...style,
        }}
        className={cn(
          'z-50 overflow-hidden rounded-md border bg-popover px-3 py-1.5 text-sm text-popover-foreground shadow-md animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2',
          className
        )}
        data-side={side}
        {...props}
      />
    )

    return ReactDOM.createPortal(content, document.body)
  }
)
TooltipContent.displayName = 'TooltipContent'

export { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider }
