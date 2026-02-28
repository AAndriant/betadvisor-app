import React, { useEffect } from 'react';
import { View, Image, Text } from 'react-native';
import { User } from 'lucide-react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withTiming,
  withSequence,
} from 'react-native-reanimated';
import { cn } from '../../lib/utils';

type HaloVariant = 'gray' | 'bronze' | 'silver' | 'gold' | 'diamond';

interface HaloAvatarProps {
  imageUri?: string;
  uri?: string;
  alt?: string;
  fallback?: string;
  variant?: HaloVariant;
  premium?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function HaloAvatar({
  imageUri,
  uri,
  alt = 'Avatar',
  fallback,
  variant = 'gray',
  premium,
  size = 'md',
  className,
}: HaloAvatarProps) {
  const finalUri = uri || imageUri;
  const finalVariant = premium ? 'gold' : variant;

  const opacity = useSharedValue(1);

  useEffect(() => {
    // Pulse animation for halo
    opacity.value = withRepeat(
      withSequence(
        withTiming(0.6, { duration: 1500 }),
        withTiming(1, { duration: 1500 })
      ),
      -1,
      true
    );
  }, []);

  const animatedStyle = useAnimatedStyle(() => {
    return {
      opacity: opacity.value,
    };
  });

  const sizeClasses = {
    sm: 'w-10 h-10',
    md: 'w-14 h-14',
    lg: 'w-20 h-20',
  };

  const iconSizes = {
    sm: 16,
    md: 24,
    lg: 32,
  };

  const textSizes = {
      sm: 'text-xs',
      md: 'text-base',
      lg: 'text-xl',
  };

  const haloColors: Record<HaloVariant, string> = {
    gray: 'bg-gray-400',
    bronze: 'bg-orange-700',
    silver: 'bg-slate-300',
    gold: 'bg-yellow-400',
    diamond: 'bg-cyan-400',
  };

  return (
    <View className={cn('relative items-center justify-center', className)}>
      {/* Animated Halo Background */}
      <Animated.View
        className={cn(
          'absolute inset-0 rounded-full',
          haloColors[finalVariant]
        )}
        style={animatedStyle}
      />

      {/* Gap and Content */}
      <View className="m-[3px] rounded-full bg-slate-950 p-[2px]">
         <View
            className={cn(
              'overflow-hidden rounded-full bg-slate-800 items-center justify-center',
              sizeClasses[size]
            )}
          >
          {finalUri ? (
              <Image
              source={{ uri: finalUri }}
                accessibilityLabel={alt}
                className="w-full h-full"
                resizeMode="cover"
              />
            ) : (
              <View className="items-center justify-center w-full h-full bg-slate-800">
                {fallback ? (
                    <Text className={cn("text-white font-bold", textSizes[size])}>{fallback}</Text>
                ) : (
                    <User size={iconSizes[size]} color="#94a3b8" />
                )}
              </View>
            )}
          </View>
      </View>
    </View>
  );
}
