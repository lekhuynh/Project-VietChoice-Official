import { Message, Product } from '../../types';

interface ChatBubbleProps {
  message: Message;
  suggestions?: Product[];
}

interface ChatInterfaceState {
  messages: Message[];
  input: string;
  isLoading: boolean;
}

export type { ChatBubbleProps, ChatInterfaceState };
