import { clsx, type ClassValue } from "clsx"
import { Log } from "src/types"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}


export function formatTextToEventType(eventLog: Log): string {
  switch (eventLog.level) {
    case 'MESSAGE_COMPLETION':
      return 'Message Completion'
    case 'POST_MESSAGE_COMPLETION':
      return 'Post Message Completion'
    case 'TOOL_EXECUTION':
      return 'Tool Execution'
    case 'POST_TOOL_EXECUTION':
      return 'Post Tool Execution'
    case 'START_TURN':
      return `${printObject(eventLog.attributes, 'agent')}`
    case 'INSTRUCT':
      return `${eventLog.attributes.instruction}`
    default:
      return eventLog.level
  }
}

function printObject(obj: Record<string, unknown>, ident: string) {
  // Filter keys starting with the prefix and map their values into a formatted string
  const result = Object.keys(obj)
    .filter(key => key.startsWith(ident)) // Keep only keys starting with 'agent'
    .map(key => `${key}: ${obj[key]}`); // Format key-value pairs

  // Join the formatted strings with newlines for better readability
  return result.join('\n\n');
}