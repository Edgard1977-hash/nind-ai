import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, ArrowUp, X, Loader2, Search, ChevronRight, ChevronLeft, Check } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";
import ProfilePage from "../components/custom/ProfilePage";
import { getTranslation } from "../utils/translations";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Logo SVG component
const LogoSvg = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="25 130 1360 420" className={className}>
    <g>
      <path d="M 97.00 546.37 C64.96,542.61 38.70,519.91 29.71,488.20 C27.57,480.64 27.52,479.13 27.23,405.59 C26.95,333.02 27.00,330.43 28.98,322.59 C36.12,294.22 57.79,272.03 85.13,265.08 C104.06,260.27 118.50,261.95 137.00,271.12 C146.08,275.62 148.73,277.56 156.64,285.46 C166.43,295.25 172.10,304.58 176.02,317.36 C179.55,328.87 180.00,338.89 179.99,404.97 C179.99,483.75 179.58,487.79 169.77,506.21 C164.02,517.01 149.05,531.58 137.45,537.68 C125.31,544.06 108.34,547.70 97.00,546.37 ZM 260.50 503.84 C242.54,500.46 231.50,494.62 218.44,481.56 C207.83,470.94 203.62,464.34 198.99,451.00 C195.93,442.19 195.16,423.24 195.07,354.47 C194.98,286.29 195.32,283.21 204.83,264.50 C208.58,257.11 211.10,253.81 218.95,246.00 C229.80,235.21 236.28,231.02 248.77,226.73 C255.78,224.32 259.72,223.63 268.78,223.24 C282.25,222.65 290.32,224.26 302.63,229.98 C320.14,238.12 332.34,250.33 339.87,267.27 C346.44,282.04 347.06,288.80 347.69,353.00 C348.44,430.46 347.23,445.08 338.57,462.50 C331.58,476.58 321.19,487.69 308.04,495.15 C293.79,503.24 275.30,506.62 260.50,503.84 ZM 1209.50 500.98 C1182.05,497.49 1154.42,481.64 1137.67,459.76 C1122.41,439.83 1113.49,419.15 1109.52,394.47 C1107.54,382.16 1107.51,350.71 1109.46,338.78 C1117.87,287.48 1152.09,246.54 1196.00,235.25 C1205.58,232.79 1208.16,232.55 1225.50,232.53 C1242.33,232.51 1245.47,232.78 1253.00,234.84 C1267.96,238.93 1284.16,248.64 1289.31,256.59 C1290.51,258.45 1291.84,259.98 1292.25,259.99 C1292.66,259.99 1293.00,233.03 1293.00,200.06 C1293.00,153.20 1293.27,139.94 1294.25,139.31 C1294.94,138.86 1313.89,138.37 1336.36,138.21 C1372.09,137.95 1377.52,138.11 1379.61,139.48 L 1382.00 141.05 L 1382.00 316.94 C1382.00,413.68 1381.73,493.55 1381.39,494.42 C1380.85,495.83 1376.13,496.00 1338.41,496.00 L 1296.04 496.00 L 1295.38 493.38 C1295.02,491.93 1294.97,486.49 1295.29,481.29 L 1295.85 471.82 L 1290.44 477.81 C1281.22,487.99 1266.13,496.25 1250.53,499.65 C1242.13,501.49 1219.28,502.23 1209.50,500.98 ZM 1257.84 425.55 C1272.94,421.54 1284.68,408.23 1290.63,388.40 C1293.37,379.26 1293.14,352.90 1290.24,343.81 C1283.13,321.53 1268.48,308.09 1249.38,306.31 C1238.34,305.28 1226.06,308.93 1217.25,315.87 C1205.18,325.38 1195.96,347.79 1196.01,367.50 C1196.06,387.92 1206.51,410.38 1220.42,419.94 C1230.00,426.54 1245.44,428.85 1257.84,425.55 ZM 412.61 494.42 C411.57,491.72 411.94,240.65 412.98,239.00 C413.80,237.71 419.62,237.50 455.38,237.50 C478.18,237.50 497.08,237.75 497.39,238.06 C497.70,238.37 498.08,243.54 498.23,249.56 L 498.50 260.50 L 506.50 252.45 C515.47,243.43 523.79,238.51 536.02,234.98 C545.40,232.27 569.68,231.16 580.99,232.93 C618.09,238.71 642.85,263.57 652.28,304.50 C654.28,313.19 654.37,316.68 654.72,404.76 L 655.08 496.02 L 611.29 495.76 L 567.50 495.50 L 566.99 416.50 C566.48,338.17 566.45,337.44 564.25,331.00 C561.17,321.98 555.79,315.16 549.00,311.68 C543.78,309.00 542.94,308.88 532.50,309.20 C522.57,309.52 521.04,309.82 516.77,312.36 C511.35,315.58 507.35,319.95 505.21,325.00 C501.17,334.55 501.07,336.69 501.04,417.75 L 501.00 496.00 L 457.11 496.00 C418.00,496.00 413.15,495.83 412.61,494.42 ZM 700.41 494.85 C699.30,493.07 699.46,240.13 700.56,239.08 C701.08,238.59 720.55,238.04 743.83,237.85 C784.79,237.51 786.21,237.56 787.58,239.44 C788.79,241.09 789.00,259.96 788.99,366.44 C788.98,435.22 788.70,492.51 788.37,493.75 L 787.77 496.00 L 744.44 496.00 C712.79,496.00 700.93,495.69 700.41,494.85 ZM 835.51 492.75 C834.59,487.65 835.40,239.27 836.33,238.33 C837.25,237.42 919.49,237.15 920.40,238.07 C920.71,238.38 921.09,243.55 921.23,249.57 L 921.50 260.50 L 929.50 252.39 C936.02,245.78 939.07,243.54 946.00,240.26 C960.84,233.25 964.90,232.49 987.00,232.56 C1005.32,232.62 1007.04,232.79 1015.45,235.36 C1043.32,243.90 1062.09,262.76 1071.54,291.72 C1077.68,310.54 1077.40,305.29 1077.75,404.76 L 1078.08 496.02 L 1034.29 495.76 L 990.50 495.50 L 990.00 416.00 L 989.50 336.50 L 987.18 330.76 C982.45,319.04 976.22,312.27 968.12,310.02 C963.36,308.69 950.98,308.72 945.69,310.07 C935.91,312.56 929.03,320.19 925.93,332.01 C924.10,338.98 924.00,343.51 924.00,417.68 L 924.00 496.00 L 880.05 496.00 L 836.09 496.00 L 835.51 492.75 ZM 700.25 216.34 C699.28,215.95 699.00,207.43 699.00,178.47 L 699.00 141.11 L 701.22 139.56 C703.15,138.21 708.97,138.00 744.57,138.00 C783.14,138.00 785.79,138.11 787.35,139.83 C788.82,141.46 789.00,145.64 789.00,178.72 C789.00,211.60 788.82,215.85 787.42,216.39 C785.53,217.12 702.05,217.06 700.25,216.34 Z" fill="currentColor"/>
    </g>
  </svg>
);

// Search icon SVG (user's custom)
const SearchIconCustom = ({ className }) => (
  <svg viewBox="0 0 1024 1024" fill="currentColor" className={className}>
    <path d="M 836.00 852.40 C820.81,849.66 814.26,845.70 792.75,826.24 C766.95,802.89 756.60,793.45 729.95,768.93 C717.05,757.06 698.17,739.78 688.00,730.52 C677.83,721.26 663.88,708.44 657.00,702.03 C650.12,695.63 634.71,681.27 622.74,670.12 L 600.98 649.85 L 590.24 656.62 C575.76,665.74 553.24,676.81 537.85,682.37 C492.55,698.73 443.36,703.39 393.36,696.05 C337.77,687.89 283.52,662.02 240.20,623.00 C190.47,578.20 156.55,511.80 150.08,446.58 C148.54,430.96 148.74,399.68 150.50,384.70 C158.02,320.39 186.33,263.35 232.83,218.83 C303.86,150.83 400.77,124.09 498.00,145.66 C535.80,154.04 574.87,172.12 607.00,196.07 C703.17,267.78 743.77,389.25 709.43,502.53 C701.93,527.28 691.32,549.57 676.18,572.42 L 667.62 585.33 L 672.06 589.32 C674.50,591.51 699.45,613.42 727.50,638.02 C755.55,662.63 787.50,690.75 798.50,700.53 C809.50,710.30 829.75,728.28 843.50,740.49 C879.34,772.30 883.32,776.36 887.73,785.65 C890.87,792.27 891.46,794.63 891.82,802.04 C892.04,806.80 891.73,813.05 891.11,815.92 C886.65,836.71 868.98,851.25 846.74,852.42 C842.21,852.66 837.38,852.65 836.00,852.40 ZM 465.81 646.48 C504.58,641.05 539.25,627.76 571.50,605.97 C593.33,591.22 615.67,568.78 631.19,546.00 C646.87,523.01 657.12,500.31 664.50,472.28 C675.64,429.96 673.42,381.68 658.36,338.74 C632.56,265.18 568.15,208.68 489.50,190.61 C471.78,186.54 456.39,184.94 435.00,184.93 C399.60,184.91 369.44,191.01 337.00,204.74 C296.83,221.74 260.26,252.12 236.07,288.57 C209.70,328.32 196.61,374.59 198.32,421.94 C199.55,456.16 206.94,485.09 222.46,516.50 C234.46,540.78 249.40,561.29 269.16,580.65 C309.19,619.84 363.85,644.16 421.50,648.41 C430.25,649.06 455.14,647.97 465.81,646.48 Z"/>
  </svg>
);

// Microphone icon
const MicIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
    <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
  </svg>
);

// Sparkles icon
const SparklesIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/>
  </svg>
);

// Person icon SVG
const PersonIcon = ({ className }) => (
  <svg viewBox="0 0 1024 1024" fill="currentColor" className={className}>
    <path d="M 472.50 907.92 C399.79,903.47 339.60,894.58 279.93,879.46 C199.83,859.17 171.51,841.57 164.58,807.79 C160.48,787.78 164.88,739.16 174.11,702.56 C193.23,626.76 238.62,581.38 324.50,552.17 C343.87,545.58 372.91,539.00 382.61,539.00 C386.12,539.00 388.26,539.88 393.73,543.58 C413.47,556.94 443.76,567.65 476.00,572.66 C490.33,574.89 528.58,575.18 543.00,573.16 C577.95,568.29 607.96,557.82 630.43,542.68 L 636.37 538.68 L 646.06 539.81 C665.43,542.08 703.65,553.48 727.57,564.12 C788.29,591.11 823.84,627.19 843.22,681.50 C856.66,719.16 864.59,779.85 859.54,806.52 C853.77,837.05 831.12,853.72 770.58,871.98 C708.99,890.55 632.18,903.33 554.29,907.97 C534.80,909.14 491.96,909.10 472.50,907.92 ZM 491.00 493.36 C422.58,484.88 365.71,437.02 344.05,369.72 C338.60,352.77 336.94,342.22 336.31,320.50 C335.48,291.89 338.48,271.23 346.61,249.61 C361.87,208.97 393.61,173.73 432.51,154.20 C474.35,133.20 527.65,130.25 571.51,146.49 C629.04,167.79 671.99,217.51 684.59,277.39 C688.07,293.95 688.98,322.12 686.57,339.27 C679.49,389.87 653.55,433.03 612.50,462.55 C601.94,470.14 579.28,481.64 566.50,485.89 C548.85,491.76 539.55,493.16 516.00,493.49 C504.17,493.66 492.92,493.60 491.00,493.36 Z"/>
  </svg>
);

// Upgrade icon SVG
const UpgradeIcon = ({ className }) => (
  <svg viewBox="0 0 1024 1024" fill="currentColor" className={className}>
    <path d="M 501.40 832.12 C495.40,830.07 491.71,827.38 487.25,821.78 C480.59,813.45 481.00,826.00 481.00,628.53 L 481.00 449.43 L 448.25 482.29 C430.24,500.36 413.70,516.20 411.50,517.50 C392.69,528.57 367.00,513.54 367.00,491.45 C367.00,479.08 364.80,481.69 432.92,413.30 C472.84,373.23 496.42,350.29 499.19,348.82 C502.64,346.99 505.11,346.53 511.57,346.52 C525.33,346.49 523.04,344.59 591.85,413.15 C638.28,459.41 653.29,474.95 655.11,478.65 C658.63,485.80 658.49,497.50 654.79,504.59 C651.56,510.78 646.39,515.48 639.18,518.77 C634.57,520.88 632.73,521.18 626.64,520.78 C621.98,520.48 617.94,519.53 615.00,518.05 C611.95,516.51 599.66,504.92 576.76,481.96 L 543.02 448.14 L 542.76 630.32 L 542.50 812.50 L 539.50 817.92 C532.18,831.15 516.11,837.14 501.40,832.12 ZM 369.92 791.05 C355.32,786.62 321.88,764.79 296.50,743.10 C263.75,715.13 235.47,679.27 214.70,639.41 C206.68,624.01 195.13,589.00 190.49,566.06 C177.49,501.67 184.77,430.58 210.09,374.75 C238.28,312.60 285.53,261.59 348.28,225.56 C357.94,220.02 389.61,205.00 391.65,205.00 C392.03,205.00 395.09,203.90 398.45,202.56 C416.80,195.21 450.44,187.54 478.00,184.41 C495.62,182.41 536.90,182.97 554.75,185.46 C586.26,189.85 614.69,197.50 640.52,208.53 C713.98,239.91 772.39,293.18 807.14,360.50 C825.70,396.47 836.01,432.75 838.95,472.50 C844.99,553.96 824.08,628.59 778.15,689.50 C748.26,729.13 704.08,766.72 662.50,787.92 C655.93,791.26 654.91,791.48 646.00,791.49 C637.48,791.49 635.94,791.19 631.07,788.63 C624.16,785.01 618.90,779.53 615.32,772.24 C612.94,767.40 612.50,765.25 612.50,758.50 C612.50,751.70 612.93,749.62 615.39,744.61 C619.40,736.46 624.02,732.22 635.04,726.59 C691.95,697.52 735.68,650.52 757.91,594.52 C777.38,545.48 781.26,487.89 768.43,438.26 C756.09,390.55 734.83,353.13 699.00,316.03 C684.40,300.92 659.69,283.55 635.03,271.07 C605.30,256.02 581.43,248.54 545.00,242.83 C531.73,240.75 488.50,241.10 474.00,243.40 C427.61,250.75 387.91,267.38 351.00,294.91 C285.81,343.52 246.43,425.85 249.32,507.50 C251.68,574.48 277.83,634.66 324.40,680.37 C343.04,698.66 361.77,712.17 386.18,724.94 C402.00,733.22 407.41,738.15 410.95,747.55 C413.79,755.06 413.42,764.92 410.02,772.77 C407.07,779.59 398.88,787.15 391.46,789.93 C385.74,792.07 375.11,792.62 369.92,791.05 Z"/>
  </svg>
);

// Format categories
const FORMAT_TABS = ["Все", "Новые", "Видео", "Фото", "Монтаж", "Анимации"];

// Animated placeholder phrases
const PLACEHOLDER_PHRASES = [
  "Cut my video and…",
  "create logo animation for…",
  "make video story about…",
  "create motion design for…",
  "make promo video for…",
  "create short-form video for…",
  "make highlights from…",
  "create fan edit about…",
  "add visual effects in…",
  "make colour grading for…",
  "create sound effects for…",
  "Make motion graphics for…"
];

// Placeholder keys for translation
const PLACEHOLDER_KEYS = [
  'placeholder1', 'placeholder2', 'placeholder3', 'placeholder4',
  'placeholder5', 'placeholder6', 'placeholder7', 'placeholder8',
  'placeholder9', 'placeholder10', 'placeholder11', 'placeholder12'
];

// Placeholder formats with videos
const FORMATS = [
  { id: 1, name: "Reels Story", subtitle: "Vertical video for Instagram", color: "#3A3A3A", videos: [] },
  { id: 2, name: "TikTok Trend", subtitle: "Trending short-form content", color: "#4A3A5A", videos: [] },
  { id: 3, name: "Product Showcase", subtitle: "Highlight your products", color: "#3A4A5A", videos: [] },
  { id: 4, name: "Meme Format", subtitle: "Fun viral content", color: "#5A4A3A", videos: [] },
  { id: 5, name: "Before/After", subtitle: "Transformation videos", color: "#3A5A4A", videos: [] },
  { id: 6, name: "Tutorial", subtitle: "Step-by-step guides", color: "#4A4A4A", videos: [] },
  { id: 7, name: "Promo Video", subtitle: "Marketing content", color: "#5A3A4A", videos: [] },
  { id: 8, name: "Story Time", subtitle: "Narrative storytelling", color: "#3A4A4A", videos: [] },
];

// Example videos for carousel
const EXAMPLE_VIDEOS = [
  { id: 1, title: "Logo Animation", subtitle: "Brand identity motion", color: "#2A3A4A" },
  { id: 2, title: "Product Promo", subtitle: "E-commerce showcase", color: "#3A2A4A" },
  { id: 3, title: "Social Reels", subtitle: "Instagram & TikTok", color: "#4A3A2A" },
  { id: 4, title: "Event Highlights", subtitle: "Memorable moments", color: "#2A4A3A" },
  { id: 5, title: "Tutorial Video", subtitle: "Step-by-step guide", color: "#3A4A3A" },
];

export const MainPage = () => {
  const navigate = useNavigate();
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  
  // State
  const [prompt, setPrompt] = useState("");
  const [user, setUser] = useState(null);
  const [showProfile, setShowProfile] = useState(false);
  const [showFormatsPopup, setShowFormatsPopup] = useState(false);
  const [isPopupClosing, setIsPopupClosing] = useState(false);
  const [attachments, setAttachments] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [activeTab, setActiveTab] = useState("Все");
  const [searchQuery, setSearchQuery] = useState("");
  const [headerScrolled, setHeaderScrolled] = useState(false);
  
  // New states for logged-in view
  const [activeMainTab, setActiveMainTab] = useState("Formats");
  const [selectedFormat, setSelectedFormat] = useState(null);
  const [showFormatPopup, setShowFormatPopup] = useState(false);
  const [showFormatsListPopup, setShowFormatsListPopup] = useState(false);
  const [generatePrompt, setGeneratePrompt] = useState(true);
  const [userVideos, setUserVideos] = useState([]);
  const [isLoadingVideos, setIsLoadingVideos] = useState(false);
  
  // Popup swipe state
  const [popupDragY, setPopupDragY] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const popupStartY = useRef(0);

  // Examples carousel state
  const [exampleIndex, setExampleIndex] = useState(0);
  const [isCarouselTransition, setIsCarouselTransition] = useState(true);
  const touchStartX = useRef(0);
  const examplesCarouselRef = useRef(null);

  // Animated title words
  const titleWords = ['more', 'better', 'faster', 'easier'];
  const [currentWordIndex, setCurrentWordIndex] = useState(0);
  const [isWordAnimating, setIsWordAnimating] = useState(false);

  // Voice assistant state
  const [showVoiceAssistant, setShowVoiceAssistant] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isAISpeaking, setIsAISpeaking] = useState(false);
  const [voiceTranscript, setVoiceTranscript] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const recognitionRef = useRef(null);

  // Initialize Speech Recognition
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        recognitionRef.current = new SpeechRecognition();
        recognitionRef.current.continuous = true;
        recognitionRef.current.interimResults = true;
        recognitionRef.current.lang = 'ru-RU'; // Russian language

        recognitionRef.current.onresult = (event) => {
          let transcript = '';
          for (let i = event.resultIndex; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
          }
          setVoiceTranscript(transcript);
        };

        recognitionRef.current.onerror = (event) => {
          console.error('Speech recognition error:', event.error);
          setIsRecording(false);
        };

        recognitionRef.current.onend = () => {
          if (isRecording) {
            // Restart if still recording
            try {
              recognitionRef.current.start();
            } catch (e) {
              console.log('Recognition already started');
            }
          }
        };
      }
    }
  }, [isRecording]);

  // Start voice recording
  const startRecording = async () => {
    if (!recognitionRef.current) {
      alert('Speech recognition is not supported in your browser');
      return;
    }
    
    try {
      // Request microphone permission
      await navigator.mediaDevices.getUserMedia({ audio: true });
      setIsRecording(true);
      setVoiceTranscript('');
      recognitionRef.current.start();
    } catch (err) {
      console.error('Microphone access denied:', err);
      alert('Please allow microphone access to use voice commands');
    }
  };

  // Stop voice recording and process
  const stopRecording = async () => {
    setIsRecording(false);
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }

    if (voiceTranscript.trim()) {
      setIsProcessing(true);
      
      // Simulate AI processing
      setTimeout(() => {
        setIsAISpeaking(true);
        setIsProcessing(false);
        
        // Simulate video creation
        setTimeout(() => {
          setIsAISpeaking(false);
          // Set the prompt and close voice assistant
          setPrompt(voiceTranscript);
          setShowVoiceAssistant(false);
          setVoiceTranscript('');
          
          // If user is not logged in, redirect to auth
          if (!user) {
            navigate('/auth');
          }
        }, 2000);
      }, 1500);
    }
  };

  // Title word rotation effect
  useEffect(() => {
    const interval = setInterval(() => {
      setIsWordAnimating(true);
      setTimeout(() => {
        setCurrentWordIndex(prev => (prev + 1) % titleWords.length);
        setIsWordAnimating(false);
      }, 400);
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  const handleCarouselNext = () => {
    setExampleIndex(prev => Math.min(EXAMPLE_VIDEOS.length - 1, prev + 1));
  };

  const handleCarouselPrev = () => {
    setExampleIndex(prev => Math.max(0, prev - 1));
  };

  // Animated placeholder state
  const [placeholderText, setPlaceholderText] = useState("");
  const [phraseIndex, setPhraseIndex] = useState(0);
  const [isTyping, setIsTyping] = useState(true);

  // Language state
  const [currentLang, setCurrentLang] = useState(localStorage.getItem('slind_language') || 'en');

  // Translation helper
  const t = (key) => getTranslation(currentLang, key);

  const handleLanguageChange = (langCode) => {
    setCurrentLang(langCode);
  };

  // Check auth status and setup scroll listener
  useEffect(() => {
    const savedUser = localStorage.getItem("slind_user");
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        localStorage.removeItem("slind_user");
      }
    }
    
    // Scroll listener for header animation (only for non-logged in)
    const handleScroll = () => {
      const scrollY = window.scrollY;
      const threshold = 350;
      setHeaderScrolled(scrollY > threshold);
    };
    
    window.addEventListener('scroll', handleScroll);
    
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  // Fetch user videos when switching to Library tab
  useEffect(() => {
    if (activeMainTab === "Library" && user) {
      fetchUserVideos();
    }
  }, [activeMainTab, user]);

  // Animated placeholder typing effect
  useEffect(() => {
    const currentPhrase = t(PLACEHOLDER_KEYS[phraseIndex]);
    let timeout;

    if (isTyping) {
      // Typing animation
      if (placeholderText.length < currentPhrase.length) {
        timeout = setTimeout(() => {
          setPlaceholderText(currentPhrase.slice(0, placeholderText.length + 1));
        }, 50);
      } else {
        // Finished typing, wait then start erasing
        timeout = setTimeout(() => {
          setIsTyping(false);
        }, 2000);
      }
    } else {
      // Erasing animation
      if (placeholderText.length > 0) {
        timeout = setTimeout(() => {
          setPlaceholderText(placeholderText.slice(0, -1));
        }, 30);
      } else {
        // Finished erasing, move to next phrase
        setPhraseIndex((prev) => (prev + 1) % PLACEHOLDER_KEYS.length);
        setIsTyping(true);
      }
    }

    return () => clearTimeout(timeout);
  }, [placeholderText, phraseIndex, isTyping, currentLang]);

  // Reset placeholder when language changes
  useEffect(() => {
    setPlaceholderText("");
    setPhraseIndex(0);
    setIsTyping(true);
  }, [currentLang]);

  // Intersection Observer for section animations
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
          }
        });
      },
      { threshold: 0, rootMargin: '50px 0px 0px 0px' }
    );

    const titles = document.querySelectorAll('.section-title, .section-subtitle');
    titles.forEach((el) => observer.observe(el));

    return () => {
      titles.forEach((el) => observer.unobserve(el));
    };
  }, [user]);

  const fetchUserVideos = async () => {
    if (!user?.user_id) return;
    setIsLoadingVideos(true);
    try {
      const response = await axios.get(`${API}/videos/user/${user.user_id}`);
      setUserVideos(response.data.projects || []);
    } catch (error) {
      console.error("Failed to fetch videos:", error);
    } finally {
      setIsLoadingVideos(false);
    }
  };

  const handleSubmit = async () => {
    if (!user) {
      navigate('/auth');
      return;
    }
    
    if (!prompt.trim() && attachments.length === 0) return;
    
    setIsGenerating(true);
    
    try {
      const requestData = {
        prompt: prompt.trim(),
        format_id: selectedFormat?.id || "auto",
        language: "auto"
      };
      
      if (attachments.length > 0) {
        const uploadedUrls = [];
        for (const att of attachments) {
          if (att.file && !att.uploadedUrl) {
            const formData = new FormData();
            formData.append("file", att.file);
            const uploadRes = await axios.post(`${API}/upload`, formData, {
              headers: { "Content-Type": "multipart/form-data" }
            });
            uploadedUrls.push(uploadRes.data.url);
          } else if (att.uploadedUrl) {
            uploadedUrls.push(att.uploadedUrl);
          }
        }
        
        const videoAttachment = attachments.find(a => a.type === "video");
        if (videoAttachment && uploadedUrls.length > 0) {
          const response = await axios.post(`${API}/device-mockup/create`, {
            video_url: uploadedUrls[0],
            device_type: "phone",
            rotation: 12,
            bg_color: [15, 15, 20],
            animation_style: "camera",
            phone_position: "center",
            aspect_ratio: "9:16"
          });
          
          toast.success("Создаём 3D анимацию...");
          navigate(`/video/${response.data.id}`);
          return;
        }
        
        requestData.product_images = uploadedUrls;
      }
      
      const response = await axios.post(`${API}/video/generate`, requestData);
      toast.success("Генерация началась!");
      navigate(`/video/${response.data.id}`);
    } catch (error) {
      console.error("Failed to start generation:", error);
      toast.error("Ошибка при запуске генерации");
      setIsGenerating(false);
    }
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    
    files.forEach(file => {
      const id = Date.now() + Math.random();
      const isVideo = file.type.startsWith("video/");
      
      const reader = new FileReader();
      reader.onload = (event) => {
        setAttachments(prev => [...prev, {
          id,
          type: isVideo ? "video" : "image",
          preview: event.target.result,
          file,
          uploading: false,
          progress: 0
        }]);
      };
      reader.readAsDataURL(file);
    });
    
    e.target.value = "";
  };

  const removeAttachment = (id) => {
    setAttachments(prev => prev.filter(a => a.id !== id));
  };

  const handleUpdateUser = (updatedUser) => {
    setUser(updatedUser);
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem("slind_user");
    setShowProfile(false);
  };

  const handleGetStarted = () => {
    navigate('/auth');
  };

  const handleAvatarClick = () => {
    if (user) {
      setShowProfile(true);
    } else {
      navigate('/auth');
    }
  };

  const handleClosePopup = () => {
    setIsPopupClosing(true);
    setTimeout(() => {
      setShowFormatsPopup(false);
      setIsPopupClosing(false);
    }, 300);
  };

  const handleSelectFormat = (format) => {
    setShowFormatPopup(true);
    setSelectedFormat(format);
  };

  const handleUseFormat = () => {
    setShowFormatPopup(false);
  };

  // Swipe handlers for popups
  const handlePopupTouchStart = (e) => {
    popupStartY.current = e.touches[0].clientY;
    setIsDragging(true);
  };

  const handlePopupTouchMove = (e) => {
    if (!isDragging) return;
    const diff = e.touches[0].clientY - popupStartY.current;
    if (diff > 0) setPopupDragY(diff);
  };

  const handlePopupTouchEnd = (closePopup) => {
    setIsDragging(false);
    if (popupDragY > 100) {
      closePopup();
    }
    setPopupDragY(0);
  };

  // Show profile page
  if (showProfile && user) {
    return (
      <ProfilePage 
        user={user} 
        onBack={() => setShowProfile(false)}
        onLogout={handleLogout}
        onUpdateUser={handleUpdateUser}
        currentLang={currentLang}
        onLanguageChange={handleLanguageChange}
      />
    );
  }

  const completedVideos = userVideos.filter(v => v.status === 'completed');

  // ============ LOGGED IN VIEW ============
  if (user) {
    return (
      <div className="main-page-fixed" data-testid="main-page-logged">
        {/* Background Grid */}
        <div className="perspective-grid">
          <svg viewBox="0 0 400 300" preserveAspectRatio="none" className="grid-svg">
            <line x1="0" y1="0" x2="0" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
            <line x1="80" y1="0" x2="80" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
            <line x1="160" y1="0" x2="160" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
            <line x1="240" y1="0" x2="240" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
            <line x1="320" y1="0" x2="320" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
            <line x1="400" y1="0" x2="400" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
            
            <path d="M0,0 Q200,0 400,0" stroke="rgba(255,255,255,0.06)" strokeWidth="1" fill="none"/>
            <path d="M0,75 Q200,65 400,75" stroke="rgba(255,255,255,0.07)" strokeWidth="1" fill="none"/>
            <path d="M0,150 Q200,130 400,150" stroke="rgba(255,255,255,0.08)" strokeWidth="1" fill="none"/>
            <path d="M0,225 Q200,195 400,225" stroke="rgba(255,255,255,0.09)" strokeWidth="1" fill="none"/>
            <path d="M0,300 Q200,260 400,300" stroke="rgba(255,255,255,0.1)" strokeWidth="1" fill="none"/>
          </svg>
        </div>
        
        {/* Fixed Header */}
        <header className="main-fixed-header">
          <div className="header-left-logo">
            <LogoSvg className="header-logo-svg" />
          </div>
          
          <div className="header-right-actions">
            <button 
              className="header-upgrade-btn"
              onClick={() => {/* TODO: Upgrade flow */}}
              data-testid="upgrade-btn"
            >
              <UpgradeIcon className="upgrade-btn-icon" />
              Upgrade
            </button>
            
            <button 
              className="header-avatar-btn"
              onClick={handleAvatarClick}
              data-testid="header-avatar-btn"
            >
              {user.picture ? (
                <img src={user.picture} alt={user.name} />
              ) : (
                <span>{(user.name || user.email)?.[0]?.toUpperCase()}</span>
              )}
            </button>
          </div>
        </header>

        {/* Content - always Create view */}
        <div className="create-content-v2">
            {/* Center section - heading and input */}
            <div className="create-center-section">
              {/* Heading */}
              <div className="create-heading">
                <h1 className="create-title">
                  {t('readyToCreate')}
                </h1>
              </div>

              {/* Input area */}
              <div className="create-input-area">
                <div className={`input-outer ${isUploading ? "uploading" : ""}`}>
                  {attachments.length > 0 && (
                    <div className="attachments-row">
                      {attachments.map((attachment) => (
                        <div key={attachment.id} className="attachment-item">
                          <img 
                            src={attachment.preview} 
                            alt="Attachment" 
                            className="attachment-preview"
                          />
                          <button 
                            className="attachment-remove"
                            onClick={() => removeAttachment(attachment.id)}
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="input-inner">
                    <textarea
                      ref={textareaRef}
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      placeholder={`nind ai, ${placeholderText}`}
                      className="prompt-textarea"
                      rows={2}
                      disabled={isGenerating}
                      data-testid="prompt-input"
                    />
                </div>

                <div className="input-bottom-row">
                  <button 
                    className="input-icon-btn"
                    onClick={() => fileInputRef.current?.click()}
                    data-testid="attach-button"
                  >
                    <Plus className="w-5 h-5" />
                  </button>

                  <div className="input-bottom-right">
                    <button className="input-icon-btn" data-testid="mic-button">
                      <MicIcon className="w-5 h-5" />
                    </button>
                    
                    <button 
                      className={`send-button ${prompt.trim() || attachments.length > 0 ? "active" : ""}`}
                      onClick={handleSubmit}
                      disabled={isGenerating || (!prompt.trim() && attachments.length === 0)}
                      data-testid="send-button"
                    >
                      {isGenerating ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                      ) : (
                        <ArrowUp className="w-5 h-5" />
                      )}
                    </button>
                  </div>
                </div>
                
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*,video/*"
                  multiple
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>
            </div>
            </div>

            {/* Bottom Panel with Tabs */}
            <div className="bottom-panel">
              {/* Tabs */}
              <div className="bottom-tabs-container">
                <div 
                  className="bottom-tabs-indicator"
                  style={{
                    left: activeMainTab === 'Creations' ? '4px' : '50%',
                    width: 'calc(50% - 4px)'
                  }}
                />
                <button 
                  className={`bottom-tab ${activeMainTab === 'Creations' ? 'active' : ''}`}
                  onClick={() => setActiveMainTab('Creations')}
                  data-testid="creations-tab"
                >
                  {t('myCreations')}
                </button>
                <button 
                  className={`bottom-tab ${activeMainTab === 'Formats' ? 'active' : ''}`}
                  onClick={() => setActiveMainTab('Formats')}
                  data-testid="formats-tab"
                >
                  {t('formats')}
                </button>
              </div>

              {/* Content */}
              <div className="bottom-panel-content">
                {activeMainTab === 'Formats' ? (
                  <>
                    <div className="formats-grid-logged">
                      {FORMATS.slice(0, 8).map((format) => (
                        <button 
                          key={format.id}
                          className="format-card-carousel-btn"
                          onClick={() => handleSelectFormat(format)}
                          data-testid={`create-format-${format.id}`}
                        >
                          <div 
                            className="format-card-bg"
                            style={{ backgroundColor: format.color }}
                          />
                          <div className="format-card-gradient" />
                          <span className="format-card-name">{format.name}</span>
                        </button>
                      ))}
                    </div>
                    
                    <button 
                      className="create-see-all-btn"
                      onClick={() => navigate('/formats')}
                      data-testid="create-see-all-btn"
                    >
                      {t('seeAll')}
                    </button>
                  </>
                ) : (
                  /* My Creations */
                  <>
                    {isLoadingVideos ? (
                      <div className="library-loading">Loading...</div>
                    ) : completedVideos.length > 0 ? (
                      <div className="creations-grid-real">
                        {completedVideos.map((video) => (
                          <div 
                            key={video.id} 
                            className="creation-card"
                            onClick={() => navigate(`/video/${video.id}`)}
                            data-testid={`library-video-${video.id}`}
                          >
                            {video.poster_url ? (
                              <img 
                                src={`${BACKEND_URL}${video.poster_url}`} 
                                alt={video.title || 'Video'}
                              />
                            ) : video.video_url ? (
                              <video 
                                src={`${BACKEND_URL}${video.video_url}`}
                                muted
                                playsInline
                              />
                            ) : (
                              <div className="creation-placeholder" />
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="creations-empty-pattern">
                        <div className="creations-pattern-grid">
                          {/* Left column */}
                          <div className="pattern-column">
                            <div className="pattern-item ratio-9-16" />
                            <div className="pattern-item ratio-1-1" />
                            <div className="pattern-item ratio-16-9" />
                            <div className="pattern-item ratio-9-16" />
                          </div>
                          {/* Right column */}
                          <div className="pattern-column">
                            <div className="pattern-item ratio-16-9" />
                            <div className="pattern-item ratio-9-16" />
                            <div className="pattern-item ratio-1-1" />
                            <div className="pattern-item ratio-16-9" />
                          </div>
                        </div>
                        <div className="creations-empty-fade" />
                        <div className="creations-empty-overlay">
                          <p className="creations-empty-text">{t('noVideosYet')}</p>
                          <button 
                            className="creations-start-btn"
                            onClick={() => {
                              window.scrollTo({ top: 0, behavior: 'smooth' });
                              setTimeout(() => textareaRef.current?.focus(), 500);
                            }}
                            data-testid="start-create-btn"
                          >
                            {t('startCreate')}
                          </button>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>

        {/* Format Detail Popup */}
        {showFormatPopup && selectedFormat && (
          <div 
            className="format-popup-overlay"
            onClick={() => setShowFormatPopup(false)}
          >
            <div 
              className="format-detail-popup"
              style={{ transform: `translateY(${popupDragY}px)` }}
              onClick={(e) => e.stopPropagation()}
              onTouchStart={handlePopupTouchStart}
              onTouchMove={handlePopupTouchMove}
              onTouchEnd={() => handlePopupTouchEnd(() => setShowFormatPopup(false))}
            >
              <div className="popup-drag-handle" />
              
              {/* Videos carousel */}
              <div className="format-videos-row">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="format-video-item">
                    <div 
                      className="format-video-placeholder"
                      style={{ backgroundColor: selectedFormat.color }}
                    />
                  </div>
                ))}
              </div>
              
              {/* Format name */}
              <h3 className="format-detail-name">{selectedFormat.name}</h3>
              
              {/* Generate prompt checkbox */}
              <label className="generate-prompt-row" onClick={() => setGeneratePrompt(!generatePrompt)}>
                <div className={`custom-checkbox ${generatePrompt ? 'checked' : ''}`}>
                  {generatePrompt && <Check className="check-icon" />}
                </div>
                <span>Generate prompt</span>
              </label>
              
              {/* Use button */}
              <button 
                className="format-use-btn"
                onClick={handleUseFormat}
                data-testid="format-use-btn"
              >
                <SparklesIcon className="sparkles-icon" />
                <span>Use</span>
              </button>
            </div>
          </div>
        )}

        {/* Formats List Popup (search) */}
        {showFormatsListPopup && (
          <div 
            className="format-popup-overlay"
            onClick={() => setShowFormatsListPopup(false)}
          >
            <div 
              className="formats-list-popup"
              style={{ transform: `translateY(${popupDragY}px)` }}
              onClick={(e) => e.stopPropagation()}
              onTouchStart={handlePopupTouchStart}
              onTouchMove={handlePopupTouchMove}
              onTouchEnd={() => handlePopupTouchEnd(() => setShowFormatsListPopup(false))}
            >
              <div className="popup-drag-handle" />
              
              <h2 className="formats-list-title">Formats</h2>
              
              <div className="formats-list-grid">
                {FORMATS.map((format) => (
                  <button 
                    key={format.id}
                    className="formats-list-item"
                    onClick={() => {
                      handleSelectFormat(format);
                      setShowFormatsListPopup(false);
                    }}
                    data-testid={`formats-list-${format.id}`}
                  >
                    <div 
                      className="formats-list-thumb"
                      style={{ backgroundColor: format.color }}
                    />
                    <span className="formats-list-name">{format.name}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ============ NOT LOGGED IN VIEW (ORIGINAL) ============
  return (
    <div className="main-page" data-testid="main-page">
      {/* Background */}
      <div className="liquid-gradient-bg" />
      
      {/* Perspective Grid */}
      <div className="perspective-grid">
        <svg viewBox="0 0 400 300" preserveAspectRatio="none" className="grid-svg">
          <line x1="0" y1="0" x2="0" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          <line x1="80" y1="0" x2="80" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          <line x1="160" y1="0" x2="160" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          <line x1="240" y1="0" x2="240" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          <line x1="320" y1="0" x2="320" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          <line x1="400" y1="0" x2="400" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          
          <path d="M0,0 Q200,0 400,0" stroke="rgba(255,255,255,0.06)" strokeWidth="1" fill="none"/>
          <path d="M0,75 Q200,65 400,75" stroke="rgba(255,255,255,0.07)" strokeWidth="1" fill="none"/>
          <path d="M0,150 Q200,130 400,150" stroke="rgba(255,255,255,0.08)" strokeWidth="1" fill="none"/>
          <path d="M0,225 Q200,195 400,225" stroke="rgba(255,255,255,0.09)" strokeWidth="1" fill="none"/>
          <path d="M0,300 Q200,260 400,300" stroke="rgba(255,255,255,0.1)" strokeWidth="1" fill="none"/>
        </svg>
      </div>
      
      {/* Fixed Header with blur */}
      <header className={`fixed-header ${headerScrolled ? 'scrolled' : ''}`}>
        <div className="header-blur" />
        <div className="header-content">
          <div className={`logo-container ${headerScrolled ? 'hidden' : ''}`}>
            <LogoSvg className="logo-svg" />
          </div>
          
          <span className={`header-overview-text ${headerScrolled ? 'visible' : ''}`}>Overview</span>
          
          <button 
            className={`get-started-btn ${headerScrolled ? 'hidden' : ''}`}
            onClick={handleGetStarted}
            data-testid="get-started-btn"
          >
            {t('getStarted')}
          </button>
        </div>
      </header>

      {/* Main content - scrollable */}
      <div className="main-content">
        {/* Center section - same layout as logged in */}
        <div className="create-center-section-landing">
          {/* Heading */}
          <div className="create-heading">
            <h1 className="create-title">Create smarter</h1>
            <p className="create-subtitle">{t('makeVideoEditing')}</p>
          </div>

          {/* Input area */}
          <div className="create-input-area">
          <div className={`input-outer ${isUploading ? "uploading" : ""}`}>
            {attachments.length > 0 && (
              <div className="attachments-row">
                {attachments.map((attachment) => (
                  <div key={attachment.id} className="attachment-item">
                    {attachment.type === "video" && attachment.uploading ? (
                      <div className="attachment-uploading">
                        <div 
                          className="attachment-preview-blur"
                          style={{ backgroundImage: `url(${attachment.preview})` }}
                        />
                        <span className="upload-progress">{Math.round(attachment.progress)}%</span>
                      </div>
                    ) : (
                      <img 
                        src={attachment.preview} 
                        alt="Attachment" 
                        className="attachment-preview"
                      />
                    )}
                    <button 
                      className="attachment-remove"
                      onClick={() => removeAttachment(attachment.id)}
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div className="input-inner">
              <textarea
                ref={textareaRef}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder={`nind ai, ${placeholderText}`}
                className="prompt-textarea"
                rows={2}
                disabled={isGenerating}
                data-testid="prompt-input"
              />
            </div>

            <div className="input-bottom-row">
              <button 
                className="input-icon-btn"
                onClick={() => navigate('/auth')}
                data-testid="attach-button"
              >
                <Plus className="w-5 h-5" />
              </button>

              <div className="input-bottom-right">
                <button 
                  className="input-icon-btn" 
                  onClick={() => setShowVoiceAssistant(true)}
                  data-testid="mic-button"
                >
                  <MicIcon className="w-5 h-5" />
                </button>
                
                <button 
                  className={`send-button ${prompt.trim() || attachments.length > 0 ? "active" : ""}`}
                  onClick={() => navigate('/auth')}
                  data-testid="send-button"
                >
                  <ArrowUp className="w-5 h-5" />
                </button>
              </div>
            </div>
            
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*,video/*"
              multiple
              onChange={handleFileSelect}
              className="hidden"
            />
            
            {isUploading && <div className="uploading-border" />}
          </div>
        </div>
        </div>

        {/* Black section wrapper - everything below is black */}
        <div className="black-section-start">
        {/* You can do section - carousel (no title) */}
        <div className="examples-section-new">
          <div 
            className="examples-carousel-wrapper"
            ref={examplesCarouselRef}
            style={{ paddingLeft: '16px' }}
          >
            <div className="examples-carousel-inner">
              {EXAMPLE_VIDEOS.map((video, idx) => (
                <div 
                  key={video.id} 
                  className="example-card"
                >
                  <div className="example-card-content">
                    <div 
                      className="example-card-video"
                      style={{ backgroundColor: video.color }}
                    />
                    <div className="example-card-overlay">
                      <h3 className="example-card-title">{video.title}</h3>
                      <p className="example-card-subtitle">{video.subtitle}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          <div className="examples-nav-buttons-left">
            <button 
              className={`examples-nav-btn ${exampleIndex === 0 ? 'disabled' : ''}`}
              onClick={() => {
                if (exampleIndex > 0) {
                  const newIndex = exampleIndex - 1;
                  setExampleIndex(newIndex);
                  if (examplesCarouselRef.current) {
                    const card = examplesCarouselRef.current.querySelectorAll('.example-card')[newIndex];
                    if (card) {
                      const containerWidth = examplesCarouselRef.current.offsetWidth;
                      const cardLeft = card.offsetLeft;
                      const cardWidth = card.offsetWidth;
                      const scrollPos = cardLeft - (containerWidth - cardWidth) / 2;
                      examplesCarouselRef.current.scrollTo({ 
                        left: scrollPos, 
                        behavior: 'smooth' 
                      });
                    }
                  }
                }
              }}
              disabled={exampleIndex === 0}
            >
              <ChevronLeft className="w-6 h-6" />
            </button>
            <button 
              className={`examples-nav-btn ${exampleIndex === EXAMPLE_VIDEOS.length - 1 ? 'disabled' : ''}`}
              onClick={() => {
                if (exampleIndex < EXAMPLE_VIDEOS.length - 1) {
                  const newIndex = exampleIndex + 1;
                  setExampleIndex(newIndex);
                  if (examplesCarouselRef.current) {
                    const card = examplesCarouselRef.current.querySelectorAll('.example-card')[newIndex];
                    if (card) {
                      const containerWidth = examplesCarouselRef.current.offsetWidth;
                      const cardLeft = card.offsetLeft;
                      const cardWidth = card.offsetWidth;
                      const scrollPos = cardLeft - (containerWidth - cardWidth) / 2;
                      examplesCarouselRef.current.scrollTo({ 
                        left: scrollPos, 
                        behavior: 'smooth' 
                      });
                    }
                  }
                }
              }}
              disabled={exampleIndex === EXAMPLE_VIDEOS.length - 1}
            >
              <ChevronRight className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* How it works section */}
        <div className="how-section">
          <h2 className="section-title">Explore nind ai</h2>
          <div className="how-video-wrapper">
            <div className="how-video-placeholder" />
          </div>
        </div>

        {/* Discover tools section */}
        <div className="discover-tools-section">
          <h2 className="section-title">Discover tools</h2>
          
          <div className="discover-tools-grid">
            {/* AI Speech */}
            <div className="discover-tool-card">
              <div className="discover-tool-header">
                <div className="discover-tool-icon">
                  <svg viewBox="0 0 875 875" fill="currentColor">
                    <path d="M 342.54 740.95 C332.97,739.46 322.83,734.03 315.04,726.24 C311.32,722.53 307.06,717.07 305.56,714.12 C299.73,702.61 300.03,717.98 300.03,438.50 C300.03,187.70 300.08,181.31 301.97,173.82 C306.25,156.81 318.08,143.36 333.57,137.87 C340.97,135.26 353.66,134.37 361.22,135.94 C380.10,139.86 397.36,157.63 400.98,176.89 C402.39,184.36 402.39,693.68 400.98,701.11 C398.73,712.96 390.11,725.68 379.26,733.16 C369.45,739.92 355.26,742.93 342.54,740.95 ZM 519.16 635.84 C498.66,633.46 482.01,619.55 475.72,599.54 L 473.50 592.50 L 473.50 435.50 L 473.50 278.50 L 476.22 271.06 C484.26,249.02 502.82,235.59 525.00,235.76 C547.53,235.94 566.21,249.70 574.18,272.00 L 576.50 278.50 L 576.77 432.74 C577.06,602.84 577.33,594.73 570.83,608.00 C567.24,615.32 559.01,624.51 552.11,628.91 C542.84,634.82 531.28,637.25 519.16,635.84 ZM 161.62 549.89 C145.88,546.19 131.99,533.01 125.81,515.89 L 123.50 509.50 L 123.50 427.50 C123.50,352.10 123.64,344.98 125.27,339.08 C130.52,320.10 146.83,305.08 165.74,301.84 C185.57,298.44 206.57,309.23 216.36,327.87 C223.10,340.69 222.97,338.70 222.99,427.54 C223.00,514.48 223.09,513.00 217.39,524.77 C214.20,531.36 203.73,542.09 197.34,545.33 C186.80,550.66 172.63,552.47 161.62,549.89 ZM 678.10 549.42 C675.14,548.62 670.41,546.74 667.60,545.24 C660.99,541.71 651.23,531.99 647.22,524.93 C640.99,513.96 641.03,514.58 641.01,427.39 C641.01,377.99 641.38,346.25 642.02,342.89 C643.78,333.50 649.14,323.79 656.69,316.28 C664.42,308.59 670.62,304.92 680.00,302.47 C687.61,300.49 698.37,300.88 707.17,303.44 C718.67,306.80 730.48,316.98 736.30,328.57 C742.08,340.06 742.00,338.71 742.00,425.76 C742.00,475.66 741.62,507.75 740.98,511.11 C737.59,529.11 722.96,544.91 705.47,549.47 C698.17,551.37 685.27,551.34 678.10,549.42 Z"/>
                  </svg>
                </div>
                <span className="discover-tool-title">AI Speech</span>
              </div>
              <span className="discover-tool-subtitle">Generating AI-voiceover</span>
            </div>
            
            {/* AI Soundtrack */}
            <div className="discover-tool-card">
              <div className="discover-tool-header">
                <div className="discover-tool-icon">
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
                  </svg>
                </div>
                <span className="discover-tool-title">AI Soundtrack</span>
              </div>
              <span className="discover-tool-subtitle">Generating sound effects and music</span>
            </div>
            
            {/* AI Translation */}
            <div className="discover-tool-card">
              <div className="discover-tool-header">
                <div className="discover-tool-icon">
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                  </svg>
                </div>
                <span className="discover-tool-title">AI Translation</span>
              </div>
              <span className="discover-tool-subtitle">Video translation with AI-voiceover or subtitles</span>
            </div>
            
            {/* AI Cut */}
            <div className="discover-tool-card">
              <div className="discover-tool-header">
                <div className="discover-tool-icon">
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M18 4l2 4h-3l-2-4h-2l2 4h-3l-2-4H8l2 4H7L5 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V4h-4z"/>
                  </svg>
                </div>
                <span className="discover-tool-title">AI Cut</span>
              </div>
              <span className="discover-tool-subtitle">Cutting video with AI</span>
            </div>
            
            {/* AI Script */}
            <div className="discover-tool-card">
              <div className="discover-tool-header">
                <div className="discover-tool-icon">
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/>
                  </svg>
                </div>
                <span className="discover-tool-title">AI Script</span>
              </div>
              <span className="discover-tool-subtitle">Generating script for video</span>
            </div>
            
            {/* AI Color grading */}
            <div className="discover-tool-card">
              <div className="discover-tool-header">
                <div className="discover-tool-icon">
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 3c-4.97 0-9 4.03-9 9s4.03 9 9 9c.83 0 1.5-.67 1.5-1.5 0-.39-.15-.74-.39-1.01-.23-.26-.38-.61-.38-.99 0-.83.67-1.5 1.5-1.5H16c2.76 0 5-2.24 5-5 0-4.42-4.03-8-9-8zm-5.5 9c-.83 0-1.5-.67-1.5-1.5S5.67 9 6.5 9 8 9.67 8 10.5 7.33 12 6.5 12zm3-4C8.67 8 8 7.33 8 6.5S8.67 5 9.5 5s1.5.67 1.5 1.5S10.33 8 9.5 8zm5 0c-.83 0-1.5-.67-1.5-1.5S13.67 5 14.5 5s1.5.67 1.5 1.5S15.33 8 14.5 8zm3 4c-.83 0-1.5-.67-1.5-1.5S16.67 9 17.5 9s1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/>
                  </svg>
                </div>
                <span className="discover-tool-title">AI Color grading</span>
              </div>
              <span className="discover-tool-subtitle">Color grading for a professional look</span>
            </div>
          </div>
        </div>

        {/* Formats section */}
        <div className="formats-section-new">
          <h2 className="section-title">See formats</h2>
          
          <div className="formats-carousel-wrapper">
            <div className="formats-carousel-inner">
              {FORMATS.slice(0, 8).map((format) => (
                <div key={format.id} className="format-card-carousel">
                  <div 
                    className="format-card-bg"
                    style={{ backgroundColor: format.color }}
                  />
                  <div className="format-card-gradient" />
                  <span className="format-card-name">{format.name}</span>
                </div>
              ))}
            </div>
          </div>
          
          <button className="formats-start-btn" onClick={() => navigate('/auth')}>
            Start create
          </button>
        </div>
        </div>
      </div>

      {/* Formats Popup */}
      {showFormatsPopup && (
        <div className={`formats-popup-overlay ${isPopupClosing ? "closing" : ""}`} onClick={handleClosePopup}>
          <div className={`formats-popup ${isPopupClosing ? "closing" : ""}`} onClick={(e) => e.stopPropagation()}>
            <div className="popup-handle" />
            
            {/* Search */}
            <div className="popup-search">
              <Search className="search-icon" />
              <input 
                type="text"
                placeholder="Найти формат контента"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input"
              />
            </div>
            
            {/* Tabs */}
            <div className="popup-tabs">
              {FORMAT_TABS.map((tab) => (
                <button
                  key={tab}
                  className={`popup-tab ${activeTab === tab ? "active" : ""}`}
                  onClick={() => setActiveTab(tab)}
                >
                  {tab}
                </button>
              ))}
            </div>
            
            {/* Grid */}
            <div className="popup-grid">
              {FORMATS.map((format) => (
                <div key={format.id} className="popup-format-card">
                  <div 
                    className="popup-format-preview"
                    style={{ backgroundColor: format.color }}
                  />
                  <span className="popup-format-name">{format.name}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Voice Assistant Overlay */}
      {showVoiceAssistant && (
        <div className="voice-assistant-overlay">
          <div className="voice-assistant-content">
            {/* AI Eyes */}
            <div className={`voice-eyes ${isAISpeaking ? 'speaking' : ''} ${isRecording ? 'listening' : ''}`}>
              <div className="voice-eye left"></div>
              <div className="voice-eye right"></div>
            </div>
            
            {/* Status Text */}
            <div className="voice-status">
              {isRecording && !voiceTranscript && <p>Слушаю...</p>}
              {isProcessing && <p>Обрабатываю запрос...</p>}
              {isAISpeaking && <p>Создаю видео по вашему запросу...</p>}
            </div>
            
            {/* Transcript */}
            {voiceTranscript && (
              <div className="voice-transcript">
                <p>"{voiceTranscript}"</p>
              </div>
            )}
          </div>
          
          {/* Bottom controls */}
          <div className="voice-controls">
            <button 
              className="voice-control-btn voice-upload-btn"
              onClick={() => {
                fileInputRef.current?.click();
              }}
            >
              <Plus className="w-6 h-6" />
            </button>
            
            <button 
              className={`voice-record-btn ${isRecording ? 'recording' : ''}`}
              onMouseDown={startRecording}
              onMouseUp={stopRecording}
              onMouseLeave={() => {
                if (isRecording) stopRecording();
              }}
              onTouchStart={(e) => {
                e.preventDefault();
                startRecording();
              }}
              onTouchEnd={(e) => {
                e.preventDefault();
                stopRecording();
              }}
            >
              <svg viewBox="0 0 24 24" fill="currentColor" className="w-8 h-8">
                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.91-3c-.49 0-.9.36-.98.85C16.52 14.2 14.47 16 12 16s-4.52-1.8-4.93-4.15c-.08-.49-.49-.85-.98-.85-.61 0-1.09.54-1 1.14.49 3 2.89 5.35 5.91 5.78V20c0 .55.45 1 1 1s1-.45 1-1v-2.08c3.02-.43 5.42-2.78 5.91-5.78.1-.6-.39-1.14-1-1.14z"/>
              </svg>
            </button>
            
            <button 
              className="voice-control-btn voice-close-btn"
              onClick={() => {
                setShowVoiceAssistant(false);
                setIsRecording(false);
                setIsAISpeaking(false);
                setVoiceTranscript('');
                setIsProcessing(false);
                if (recognitionRef.current) {
                  recognitionRef.current.stop();
                }
              }}
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default MainPage;
