import { cx } from '@/lib/utils/cva.config';

interface SocialLoginButtonProps
  extends React.ButtonHTMLAttributes<HTMLAnchorElement> {
  text?: string;
  href?: string;
}

export function SocialLoginButton({
  text = '카카오로 3초만에 시작하기',
  className,
  href,
  ...props
}: SocialLoginButtonProps) {
  return (
    <a
      href={href}
      className={cx(
        'relative flex items-center justify-center w-full h-16 gap-2 p-4 rounded-xl  bg-[#FEE500] text-[#000000] hover:bg-[#F6DC00] transition-colors',
        className
      )}
      {...props}
    >
      <span className="absolute w-6 h-6 left-4">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path
            d="M12 3.375C6.61519 3.375 2.25 6.81684 2.25 11.0625C2.25 13.8074 4.07494 16.2159 6.82013 17.576C6.67078 18.091 5.86041 20.8895 5.82816 21.1093C5.82816 21.1093 5.80875 21.2745 5.91572 21.3375C6.02269 21.4005 6.1485 21.3516 6.1485 21.3516C6.45525 21.3087 9.70566 19.0255 10.2683 18.6291C10.8303 18.7087 11.409 18.75 12 18.75C17.3848 18.75 21.75 15.3083 21.75 11.0625C21.75 6.81684 17.3848 3.375 12 3.375Z"
            fill="#17191A"
          />
        </svg>
      </span>
      <span className="text-s1">{text}</span>
    </a>
  );
}
