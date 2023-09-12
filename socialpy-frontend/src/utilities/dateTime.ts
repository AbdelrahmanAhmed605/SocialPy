function timeAgoFromString(dateString: string): string {
  const createdAt = new Date(dateString);
  const currentTime = new Date();

  const timeDifference = currentTime.getTime() - createdAt.getTime();

  const intervals: [string, number][] = [
    ['y', 31536000],
    ['m', 2592000],
    ['w', 604800],
    ['d', 86400],
    ['h', 3600],
    ['m', 60],
  ];

  for (const [unit, secondsInUnit] of intervals) {
    const delta = timeDifference / 1000 / secondsInUnit;
    if (delta >= 1) {
      return `${Math.floor(delta)}${unit}`;
    }
  }

  return 'just now';
}

export default timeAgoFromString;
