import React, { useEffect } from 'react';
import { View, Image } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withTiming,
  withSequence,
} from 'react-native-reanimated';

interface AvatarHaloProps {
  avatarUrl?: string;
  score: number;
}

export default function AvatarHalo({ avatarUrl, score }: AvatarHaloProps) {
  const pulse = useSharedValue(1);

  // Determine Halo Color based on score
  let borderColor = 'border-gray-500'; // < 50
  let isAnimated = false;

  if (score >= 90) {
    borderColor = 'border-yellow-400'; // Gold
    isAnimated = true;
  } else if (score >= 75) {
    borderColor = 'border-gray-300'; // Silver
  } else if (score >= 50) {
    borderColor = 'border-orange-400'; // Bronze/Gap
  }

  useEffect(() => {
    if (isAnimated) {
      pulse.value = withRepeat(
        withSequence(
          withTiming(1.1, { duration: 1000 }),
          withTiming(1, { duration: 1000 })
        ),
        -1,
        true
      );
    } else {
      pulse.value = 1;
    }
  }, [isAnimated]);

  const animatedStyle = useAnimatedStyle(() => {
    return {
      transform: [{ scale: pulse.value }],
    };
  });

  // Fallback for avatar
  const source = avatarUrl
    ? { uri: avatarUrl }
    : { uri: 'https://via.placeholder.com/150' };

  return (
    <View className="items-center justify-center p-4">
      <Animated.View
        className={`rounded-full p-1 border-4 ${borderColor} ${isAnimated ? 'shadow-lg shadow-yellow-500/50' : ''}`}
        style={isAnimated ? animatedStyle : {}}
      >
        <Image
          source={source}
          className="w-24 h-24 rounded-full bg-gray-200"
          resizeMode="cover"
        />
      </Animated.View>
      <View className="absolute bottom-0 bg-white dark:bg-black px-2 py-1 rounded-full border border-gray-200 shadow-sm">
         {/* Display Score Badge */}
         <Animated.Text className="font-bold text-xs">{score}</Animated.Text>
      </View>
    </View>
  );
}
