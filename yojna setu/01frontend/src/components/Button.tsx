import React from 'react';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'dark' | 'icon';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  iconLeading?: React.ReactNode;
  iconTrailing?: React.ReactNode;
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = 'primary',
      size = 'md',
      iconLeading,
      iconTrailing,
      isLoading,
      className = '',
      disabled,
      ...props
    },
    ref
  ) => {
    // Base classes common to all buttons
    const baseClasses =
      'inline-flex items-center justify-center font-semibold rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed shrink-0';

    // Variant classes
    const variantClasses: Record<ButtonVariant, string> = {
      primary:
        'bg-[#EA717B] hover:bg-[#D65D67] text-white shadow-warm-sm hover:shadow-warm-md focus:ring-[#EA717B]/40 active:scale-[0.98]',
      secondary:
        'bg-[#FFD0CA] hover:bg-[#F5B8B0] text-[#4A2525] border border-[#E8D8D2] shadow-2xs hover:border-[#D9C4BC] focus:ring-[#FFD0CA]/50 active:scale-[0.98]',
      ghost:
        'text-[#EA717B] hover:text-[#D65D67] hover:bg-[#FFD0CA]/40 focus:ring-[#FFD0CA]/50',
      dark:
        'bg-[#4A2525] hover:bg-[#3B2522] text-white shadow-warm-sm hover:shadow-warm-md focus:ring-[#4A2525]/40 active:scale-[0.98]',
      icon:
        'text-[#765E59] hover:text-[#3B2522] hover:bg-[#FFD0CA]/40 focus:ring-[#EA717B]/30',
    };

    // Size classes (icon variant handles its own padding)
    const sizeClasses: Record<ButtonSize, string> = {
      sm: variant === 'icon' ? 'p-1.5' : 'h-9 px-3.5 py-1.5 text-xs rounded-xl gap-1.5',
      md: variant === 'icon' ? 'p-2' : 'h-10 px-4 py-2 text-sm rounded-xl gap-2',
      lg: variant === 'icon' ? 'p-3' : 'h-12 px-6 py-3 text-base rounded-2xl gap-2.5',
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
        {...props}
      >
        {isLoading ? (
          <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
        ) : (
          iconLeading && <span className="shrink-0">{iconLeading}</span>
        )}
        {children}
        {!isLoading && iconTrailing && <span className="shrink-0">{iconTrailing}</span>}
      </button>
    );
  }
);

Button.displayName = 'Button';
