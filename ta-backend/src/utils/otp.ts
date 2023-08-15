export const generateOTP = () => {
  const getRandomInRange = (min: number, max: number) =>
    Math.floor(Math.random() * (max - min) + min);

  return String(getRandomInRange(100_000, 999_999));
};
