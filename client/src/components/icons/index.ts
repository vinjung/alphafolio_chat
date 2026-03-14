// icons/index.ts
import { createIcon } from './icon-wrapper';
import type { IconProps } from './icon-wrapper';

// 단일 아이콘 - 직접 SVG 파일 import
import CameraIconSvg from './camera.svg';
import CloseIconSvg from './close.svg';
import InfoIconSvg from './info.svg';
import InputClearIconSvg from './input-clear.svg';
import NewChatIconSvg from './new-chat.svg';
import ShareIconSvg from './share.svg';
import RefreshIconSvg from './refresh.svg';
import LinkIconSvg from './link.svg';
import StopIconSvg from './stop.svg';
import SendIconSvg from './send.svg';
import CheckIcon from './check.svg';
import ArrowRightIcon from './arrow-right.svg';
import SelectIcon from './select.svg';
import SearchIcon from './search.svg';
import ClearIcon from './clear.svg';

// 배리언트 있는 아이콘 - 네임스페이스로 import
import * as ProfileIcons from './profile';
import * as CopyIcons from './copy';
import * as IpaIcons from './ipa';
import * as RocketIcons from './rocket';
import * as HomeIcons from './home';
import * as DiscoverIcons from './discover';
import * as FavoriteIcons from './favorite';

// 네임스페이스 객체 내보내기
export const Icon = {
  // 단일 아이콘
  camera: createIcon(CameraIconSvg),
  close: createIcon(CloseIconSvg),
  info: createIcon(InfoIconSvg),
  inputClear: createIcon(InputClearIconSvg),
  newChat: createIcon(NewChatIconSvg),
  share: createIcon(ShareIconSvg),
  refresh: createIcon(RefreshIconSvg),
  link: createIcon(LinkIconSvg),
  stop: createIcon(StopIconSvg),
  send: createIcon(SendIconSvg),
  check: createIcon(CheckIcon),
  arrowRight: createIcon(ArrowRightIcon),
  select: createIcon(SelectIcon),
  search: createIcon(SearchIcon),
  clear: createIcon(ClearIcon),

  // 배리언트가 있는 아이콘 - 각 배리언트에 직접 createIcon 적용
  profile: {
    filled: createIcon(ProfileIcons.Filled),
    outline: createIcon(ProfileIcons.Outline),
    default: createIcon(ProfileIcons.Outline),
  },

  copy: {
    filled: createIcon(CopyIcons.Filled),
    outline: createIcon(CopyIcons.Outline),
    default: createIcon(CopyIcons.Outline),
  },

  ipa: {
    filled: createIcon(IpaIcons.Filled),
    outline: createIcon(IpaIcons.Outline),
    default: createIcon(IpaIcons.Outline),
  },

  rocket: {
    filled: createIcon(RocketIcons.Filled),
    outline: createIcon(RocketIcons.Outline),
    default: createIcon(RocketIcons.Outline),
  },

  home: {
    filled: createIcon(HomeIcons.Filled),
    outline: createIcon(HomeIcons.Outline),
    default: createIcon(HomeIcons.Outline),
  },

  discover: {
    filled: createIcon(DiscoverIcons.Filled),
    outline: createIcon(DiscoverIcons.Outline),
    default: createIcon(DiscoverIcons.Outline),
  },

  favorite: {
    filled: createIcon(FavoriteIcons.Filled),
    outline: createIcon(FavoriteIcons.Outline),
    default: createIcon(FavoriteIcons.Outline),
  },
};

// 필요한 경우 개별 아이콘 내보내기
export type { IconProps };
