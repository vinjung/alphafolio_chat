import { Text } from '@/components/shared/text';
import { Icon } from '@/components/icons';
import { Button } from '@/components/shared/button';
import { cx } from '@/lib/utils/cva.config';

interface MenuItemProps {
  title: string;
  showArrow?: boolean;
  onPress: () => void;
  className?: string;
}

export function MenuItem({
  title,
  showArrow = true,
  onPress,
  className,
}: MenuItemProps) {
  return (
    <Button
      variant="outline"
      onClick={onPress}
      className={cx('p-4 justify-between rounded-lg', className)}
      fullWidth
    >
      <Text variant="b1" className="text-neutral-900">
        {title}
      </Text>
      {showArrow && <Icon.arrowRight size={24} className="text-neutral-800" />}
    </Button>
  );
}
