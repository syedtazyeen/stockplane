import { parsePhoneNumberFromString } from "libphonenumber-js";

export const INDIAN_COUNTRY_CODE = "+91";
export const INDIAN_COUNTRY = "IN";

export function parseIndianNationalNumber(nationalNumber) {
  return parsePhoneNumberFromString(nationalNumber, INDIAN_COUNTRY);
}

export function isValidIndianMobile(nationalNumber) {
  const phone = parseIndianNationalNumber(nationalNumber);
  if (!phone?.isValid() || phone.country !== INDIAN_COUNTRY) {
    return false;
  }

  const type = phone.getType();
  return type !== "FIXED_LINE";
}

export function toIndianE164(nationalNumber) {
  const phone = parseIndianNationalNumber(nationalNumber);
  if (!phone?.isValid() || phone.country !== INDIAN_COUNTRY) {
    throw new Error("Invalid Indian phone number");
  }
  return phone.format("E.164");
}

export function parseIndianPhone(phone) {
  if (!phone) {
    return { countryCode: INDIAN_COUNTRY_CODE, nationalNumber: "" };
  }

  const parsed = parsePhoneNumberFromString(phone);
  if (parsed?.isValid() && parsed.country === INDIAN_COUNTRY) {
    return {
      countryCode: INDIAN_COUNTRY_CODE,
      nationalNumber: parsed.nationalNumber,
    };
  }

  return {
    countryCode: INDIAN_COUNTRY_CODE,
    nationalNumber: phone.replace(/\D/g, "").slice(-10),
  };
}

export function formatIndianPhone(phone) {
  const parsed = parsePhoneNumberFromString(phone);
  if (parsed?.isValid()) {
    return parsed.formatInternational();
  }

  const { countryCode, nationalNumber } = parseIndianPhone(phone);
  if (!nationalNumber) {
    return "—";
  }

  return `${countryCode} ${nationalNumber}`;
}
