import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, ArrowUp, X, Loader2, Search, ChevronRight, ChevronLeft, Check, MoreVertical, Download, Edit2, Trash2 } from "lucide-react";
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

// Plus icon (solid gray like mic)
const PlusIconSolid = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="5" x2="12" y2="19" />
    <line x1="5" y1="12" x2="19" y2="12" />
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

// Upgrade icon SVG (new from user)
const UpgradeIcon = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 551 551" className={className} fill="currentColor">
    <path d="M 247.50 535.35 C237.41,534.26 217.51,530.67 206.95,528.03 C148.40,513.36 93.94,477.03 58.19,428.78 C46.79,413.40 43.43,407.94 35.20,391.50 C17.70,356.52 9.72,324.45 8.35,283.50 C6.90,240.36 15.11,201.93 33.97,163.50 C68.19,93.79 130.00,44.87 208.34,25.48 C227.53,20.73 241.29,18.96 264.00,18.32 C338.03,16.25 403.35,40.37 457.60,89.83 C480.32,110.54 499.64,136.79 514.04,166.50 C537.15,214.21 544.10,266.54 534.40,320.00 C525.80,367.48 505.11,410.49 473.56,446.50 C465.66,455.52 465.42,455.77 454.64,465.78 C422.76,495.42 382.37,517.15 338.00,528.53 C318.24,533.60 304.28,535.20 277.50,535.49 C263.20,535.65 249.70,535.58 247.50,535.35 ZM 297.04 478.57 C328.65,474.64 356.68,465.28 381.94,450.22 C411.74,432.44 437.43,406.76 455.89,376.28 C474.13,346.18 484.00,310.07 484.00,273.41 C484.00,240.17 477.24,212.88 461.30,181.69 C434.33,128.94 385.66,90.70 325.00,74.61 C308.91,70.34 298.26,68.90 278.50,68.33 C256.05,67.68 242.26,69.16 221.61,74.45 C182.38,84.51 151.23,101.90 123.89,129.00 C82.98,169.56 63.00,216.36 63.00,271.65 C63.00,298.67 65.70,316.07 73.61,340.00 C92.24,396.37 137.10,442.37 195.95,465.46 C212.94,472.12 236.88,477.79 254.50,479.32 C265.06,480.23 286.74,479.86 297.04,478.57 ZM 261.56 413.98 C255.62,411.66 248.77,405.19 245.73,399.02 L 243.50 394.50 L 243.22 312.66 L 242.94 230.83 L 217.75 255.57 C190.48,282.35 188.36,283.88 177.45,284.76 C168.31,285.49 162.03,283.08 154.91,276.11 C148.53,269.87 146.65,265.25 146.83,256.31 C147.02,246.73 149.08,244.07 177.31,216.74 C191.66,202.86 215.03,180.02 229.24,166.00 C258.98,136.65 261.86,134.56 272.50,134.56 C278.51,134.56 280.31,135.00 284.67,137.53 C287.67,139.27 304.44,154.60 325.12,174.50 C382.24,229.48 395.07,242.28 397.18,246.38 C403.61,258.90 398.29,274.09 384.86,281.53 C380.15,284.14 378.53,284.50 371.50,284.47 C364.67,284.45 362.76,284.03 358.44,281.67 C353.23,278.81 338.22,265.27 315.42,242.86 C308.23,235.79 302.04,230.00 301.67,230.00 C301.30,230.00 301.00,267.04 301.00,312.30 L 301.00 394.61 L 298.41 399.80 C291.86,412.94 275.27,419.33 261.56,413.98 Z"/>
  </svg>
);

// Plus icon SVG (for Start button)
const PlusIcon = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="500" height="500" viewBox="0 0 500 500" className={className}>
    <path d="M 137.69 445.85 C128.67,444.81 113.18,440.11 104.50,435.75 C74.00,420.46 53.76,395.37 44.67,361.57 C42.51,353.52 42.50,353.20 42.50,245.00 L 42.50 136.50 L 45.16 126.88 C54.98,91.37 80.88,63.01 114.11,51.39 C131.06,45.47 126.42,45.69 240.00,45.27 C346.01,44.87 360.31,45.22 373.21,48.56 C401.61,55.90 426.21,74.77 440.92,100.48 C446.35,109.97 449.45,117.62 452.83,129.87 L 455.49 139.50 L 455.50 243.50 C455.50,357.78 455.72,353.21 449.35,372.00 C435.84,411.83 400.26,440.77 358.50,445.89 C347.51,447.24 149.52,447.20 137.69,445.85 ZM 365.28 397.75 C386.57,390.21 402.66,372.54 408.74,350.00 C410.36,344.01 410.50,335.74 410.50,244.00 L 410.50 144.50 L 407.26 135.21 C400.11,114.76 386.36,100.45 366.94,93.25 L 359.50 90.50 L 251.15 90.23 C144.19,89.96 142.70,89.98 135.11,92.03 C124.32,94.94 113.95,100.97 106.10,108.89 C95.06,120.02 89.38,131.84 87.07,148.45 C85.72,158.13 85.61,330.00 86.95,341.59 C90.13,369.25 107.94,390.86 134.00,398.67 L 141.50 400.92 L 249.50 400.71 L 357.50 400.50 L 365.28 397.75 ZM 240.50 355.85 C236.10,354.25 229.12,347.10 227.99,343.03 C227.43,341.01 227.01,323.32 227.01,301.75 L 227.00 264.00 L 188.16 264.00 C145.85,264.00 143.46,263.74 136.45,258.39 C131.59,254.69 128.02,247.10 128.01,240.45 C128.00,233.73 131.80,226.10 136.94,222.54 C144.54,217.27 147.08,217.00 188.66,217.00 L 227.00 217.00 L 227.02 181.75 C227.05,142.49 227.12,141.98 234.05,135.24 C242.08,127.43 256.88,128.41 264.65,137.26 C266.38,139.22 268.29,142.34 268.90,144.20 C270.14,147.95 270.77,164.00 270.91,195.69 L 271.00 216.87 L 310.25 217.19 C347.64,217.49 349.71,217.60 354.00,219.60 C363.78,224.15 368.41,231.69 367.83,242.08 C367.35,250.42 364.02,255.86 356.55,260.48 L 351.66 263.50 L 311.39 263.79 L 271.13 264.08 L 270.81 302.32 L 270.50 340.56 L 267.95 345.52 C264.39,352.42 258.00,356.32 249.64,356.68 C246.26,356.83 242.15,356.46 240.50,355.85 Z" fill="currentColor"/>
  </svg>
);
const PersonIconAvatar = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="759" height="759" viewBox="0 0 759 759" fill="white" className={className}>
    <g>
      <path d="M 343.14 701.46 C268.27,694.67 193.57,668.02 131.00,625.75 C112.00,612.92 88.11,593.93 86.00,590.00 C82.58,583.62 87.40,563.13 96.64,544.68 C119.28,499.50 165.14,462.32 228.67,437.63 C260.12,425.41 293.70,417.35 334.02,412.36 C350.82,410.28 397.56,409.98 416.50,411.83 C469.46,416.99 513.61,429.49 557.18,451.66 C599.23,473.05 631.06,499.84 650.83,530.50 C664.40,551.55 674.21,582.45 669.57,589.53 C663.47,598.84 620.39,629.94 591.00,646.25 C513.62,689.17 425.11,708.89 343.14,701.46 ZM 364.67 362.00 C295.24,355.35 240.74,306.03 225.83,236.38 C223.79,226.86 223.50,222.82 223.54,204.00 C223.57,185.49 223.89,181.04 225.84,172.00 C232.60,140.74 246.23,115.59 268.43,93.46 C289.18,72.76 312.27,59.56 340.00,52.54 C412.67,34.14 491.73,73.83 520.37,143.10 C533.46,174.78 536.37,210.31 528.51,242.76 C514.15,302.07 463.14,350.27 404.00,360.41 C392.68,362.35 375.54,363.04 364.67,362.00 Z" fill="white"/>
    </g>
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

// Smooth progress component
const SmoothProgressCard = ({ video, onStop }) => {
  const [displayProgress, setDisplayProgress] = useState(0);
  const targetProgress = Math.min(Math.floor(video.progress || 0), 99);

  useEffect(() => {
    if (displayProgress < targetProgress) {
      const diff = targetProgress - displayProgress;
      const increment = Math.max(1, Math.ceil(diff / 20));
      const timer = setTimeout(() => {
        setDisplayProgress(prev => Math.min(prev + increment, targetProgress));
      }, 50);
      return () => clearTimeout(timer);
    } else if (displayProgress > targetProgress) {
      setDisplayProgress(targetProgress);
    }
  }, [displayProgress, targetProgress]);

  return (
    <div 
      className="creation-card generating"
      data-testid={`library-video-${video.id}`}
    >
      <div className="creation-generating">
        <div className="generating-percentage">{displayProgress}%</div>
        
        <div className="generating-progress-container">
          <div 
            className="generating-progress-fill"
            style={{ width: `${displayProgress}%` }}
          />
          
          <button 
            className="generating-stop-btn"
            onClick={(e) => {
              e.stopPropagation();
              onStop && onStop(video);
            }}
            title="Stop generation"
            data-testid={`stop-generation-${video.id}`}
          >
            <div className="stop-icon" />
          </button>
        </div>
      </div>
    </div>
  );
};

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
  const [activeMainTab, setActiveMainTab] = useState("Creations");
  const [selectedFormat, setSelectedFormat] = useState(null);
  const [showFormatPopup, setShowFormatPopup] = useState(false);
  const [showFormatsListPopup, setShowFormatsListPopup] = useState(false);
  const [generatePrompt, setGeneratePrompt] = useState(true);
  const [userVideos, setUserVideos] = useState([]);
  const [generatingVideos, setGeneratingVideos] = useState([]);
  const [isLoadingVideos, setIsLoadingVideos] = useState(false);
  const [openMenu, setOpenMenu] = useState(null); // { id, top, left }
  const menuButtonRef = useRef(null);
  
  // Popup swipe state
  const [popupDragY, setPopupDragY] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const popupStartY = useRef(0);
  
  // Tick state forces "time ago" labels to refresh every 30 seconds
  const [, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 30000);
    return () => clearInterval(id);
  }, []);

  // Russian plural: "1 минута", "2 минуты", "5 минут"
  const ruPlural = (n, forms) => {
    const mod10 = n % 10;
    const mod100 = n % 100;
    if (mod10 === 1 && mod100 !== 11) return forms[0];
    if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return forms[1];
    return forms[2];
  };

  // Helper function to calculate time ago (multilingual + grammar-correct)
  const getTimeAgo = (createdAt, completedAt) => {
    // ВСЕГДА используем created_at - время когда пользователь создал видео
    const dateToUse = createdAt;
    
    if (!dateToUse) return '';
    
    const now = new Date();
    // ВАЖНО: Если дата БЕЗ timezone (нет 'Z' или '+'), добавляем 'Z' для интерпретации как UTC
    const dateStr = typeof dateToUse === 'string' ? dateToUse : dateToUse.toString();
    const dateWithTz = (dateStr.endsWith('Z') || dateStr.includes('+')) ? dateStr : dateStr + 'Z';
    const created = new Date(dateWithTz);
    
    if (isNaN(created.getTime())) {
      console.warn('[TIME_AGO] Invalid date:', dateToUse);
      return '';
    }
    
    const diffMs = Math.max(0, now - created);
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    const diffWeek = Math.floor(diffDay / 7);
    const diffMonth = Math.floor(diffDay / 30);
    const diffYear = Math.floor(diffDay / 365);

    // Get language - SAME KEY as ProfilePage uses!
    const lang = localStorage.getItem('slind_language') || user?.language || 'ru';

    const timeFormats = {
      ru: {
        justNow: 'Только что',
        secAgo: (n) => `${n} ${ruPlural(n, ['секунду', 'секунды', 'секунд'])} назад`,
        minAgo: (n) => `${n} ${ruPlural(n, ['минуту', 'минуты', 'минут'])} назад`,
        hourAgo: (n) => `${n} ${ruPlural(n, ['час', 'часа', 'часов'])} назад`,
        dayAgo: (n) => `${n} ${ruPlural(n, ['день', 'дня', 'дней'])} назад`,
        weekAgo: (n) => `${n} ${ruPlural(n, ['неделю', 'недели', 'недель'])} назад`,
        monthAgo: (n) => `${n} ${ruPlural(n, ['месяц', 'месяца', 'месяцев'])} назад`,
        yearAgo: (n) => `${n} ${ruPlural(n, ['год', 'года', 'лет'])} назад`,
      },
      en: {
        justNow: 'Just now',
        secAgo: (n) => `${n}s ago`,
        minAgo: (n) => `${n}m ago`,
        hourAgo: (n) => `${n}h ago`,
        dayAgo: (n) => `${n}d ago`,
        weekAgo: (n) => `${n}w ago`,
        monthAgo: (n) => `${n}mo ago`,
        yearAgo: (n) => `${n}y ago`,
      },
      de: {
        justNow: 'Gerade eben',
        secAgo: (n) => `vor ${n} Sek`,
        minAgo: (n) => `vor ${n} Min`,
        hourAgo: (n) => `vor ${n} Std`,
        dayAgo: (n) => `vor ${n} T`,
        weekAgo: (n) => `vor ${n} Wo`,
        monthAgo: (n) => `vor ${n} Mon`,
        yearAgo: (n) => `vor ${n} J`,
      },
      es: {
        justNow: 'Ahora mismo',
        secAgo: (n) => `hace ${n} s`,
        minAgo: (n) => `hace ${n} min`,
        hourAgo: (n) => `hace ${n} h`,
        dayAgo: (n) => `hace ${n} d`,
        weekAgo: (n) => `hace ${n} sem`,
        monthAgo: (n) => `hace ${n} mes`,
        yearAgo: (n) => `hace ${n} a`,
      },
      pt: {
        justNow: 'Agora mesmo',
        secAgo: (n) => `há ${n} s`,
        minAgo: (n) => `há ${n} min`,
        hourAgo: (n) => `há ${n} h`,
        dayAgo: (n) => `há ${n} d`,
        weekAgo: (n) => `há ${n} sem`,
        monthAgo: (n) => `há ${n} mês`,
        yearAgo: (n) => `há ${n} a`,
      },
      fr: {
        justNow: "À l'instant",
        secAgo: (n) => `il y a ${n} s`,
        minAgo: (n) => `il y a ${n} min`,
        hourAgo: (n) => `il y a ${n} h`,
        dayAgo: (n) => `il y a ${n} j`,
        weekAgo: (n) => `il y a ${n} sem`,
        monthAgo: (n) => `il y a ${n} mois`,
        yearAgo: (n) => `il y a ${n} an`,
      },
      it: {
        justNow: 'Adesso',
        secAgo: (n) => `${n} sec fa`,
        minAgo: (n) => `${n} min fa`,
        hourAgo: (n) => `${n} h fa`,
        dayAgo: (n) => `${n} g fa`,
        weekAgo: (n) => `${n} sett fa`,
        monthAgo: (n) => `${n} mes fa`,
        yearAgo: (n) => `${n} a fa`,
      },
      pl: {
        justNow: 'Przed chwilą',
        secAgo: (n) => `${n} sek temu`,
        minAgo: (n) => `${n} min temu`,
        hourAgo: (n) => `${n} godz temu`,
        dayAgo: (n) => `${n} dni temu`,
        weekAgo: (n) => `${n} tyg temu`,
        monthAgo: (n) => `${n} mies temu`,
        yearAgo: (n) => `${n} lat temu`,
      },
      tr: {
        justNow: 'Şimdi',
        secAgo: (n) => `${n} sn önce`,
        minAgo: (n) => `${n} dk önce`,
        hourAgo: (n) => `${n} sa önce`,
        dayAgo: (n) => `${n} g önce`,
        weekAgo: (n) => `${n} hf önce`,
        monthAgo: (n) => `${n} ay önce`,
        yearAgo: (n) => `${n} y önce`,
      },
      zh: {
        justNow: '刚刚',
        secAgo: (n) => `${n}秒前`,
        minAgo: (n) => `${n}分钟前`,
        hourAgo: (n) => `${n}小时前`,
        dayAgo: (n) => `${n}天前`,
        weekAgo: (n) => `${n}周前`,
        monthAgo: (n) => `${n}个月前`,
        yearAgo: (n) => `${n}年前`,
      },
      ja: {
        justNow: 'たった今',
        secAgo: (n) => `${n}秒前`,
        minAgo: (n) => `${n}分前`,
        hourAgo: (n) => `${n}時間前`,
        dayAgo: (n) => `${n}日前`,
        weekAgo: (n) => `${n}週間前`,
        monthAgo: (n) => `${n}ヶ月前`,
        yearAgo: (n) => `${n}年前`,
      },
      ar: {
        justNow: 'الآن',
        secAgo: (n) => `قبل ${n} ث`,
        minAgo: (n) => `قبل ${n} د`,
        hourAgo: (n) => `قبل ${n} س`,
        dayAgo: (n) => `قبل ${n} ي`,
        weekAgo: (n) => `قبل ${n} أ`,
        monthAgo: (n) => `قبل ${n} ش`,
        yearAgo: (n) => `قبل ${n} سنة`,
      },
    };

    const format = timeFormats[lang] || timeFormats['en'];

    if (diffSec < 10) return format.justNow;
    if (diffSec < 60) return format.secAgo(diffSec);
    if (diffMin < 60) return format.minAgo(diffMin);
    if (diffHour < 24) return format.hourAgo(diffHour);
    if (diffDay < 7) return format.dayAgo(diffDay);
    if (diffWeek < 5) return format.weekAgo(diffWeek);
    if (diffMonth < 12) return format.monthAgo(diffMonth);
    return format.yearAgo(diffYear);
  };

  // Close menu on click outside, scroll, or resize
  useEffect(() => {
    if (!openMenu) return;
    const handleClickOutside = (e) => {
      if (!e.target.closest('.creation-menu-wrapper') && !e.target.closest('.creation-menu-dropdown')) {
        setOpenMenu(null);
      }
    };
    const closeMenu = () => setOpenMenu(null);

    document.addEventListener('click', handleClickOutside);
    window.addEventListener('scroll', closeMenu, true);
    window.addEventListener('resize', closeMenu);
    return () => {
      document.removeEventListener('click', handleClickOutside);
      window.removeEventListener('scroll', closeMenu, true);
      window.removeEventListener('resize', closeMenu);
    };
  }, [openMenu]);

  // Handle stop generation — cancels the video, removes the card, restores prompt + attachments
  const handleStopGeneration = async (video) => {
    try {
      // Restore prompt + any saved attachments back into the input
      if (video.prompt) {
        setPrompt(video.prompt);
      }
      if (Array.isArray(video.savedAttachments) && video.savedAttachments.length > 0) {
        setAttachments(video.savedAttachments);
      }
      // Optimistically remove the card from UI
      setGeneratingVideos(prev => prev.filter(v => v.id !== video.id));
      // Call backend to cancel/delete the project
      try {
        await axios.delete(`${API}/videos/${video.id}`);
      } catch (err) {
        console.warn('Cancel API failed (non-fatal):', err);
      }
      toast.success('Генерация остановлена');
    } catch (e) {
      console.error('Stop failed:', e);
      toast.error('Не удалось остановить');
    }
  };

  const handleDownload = async (video) => {
    try {
      const videoUrl = video.video_url?.startsWith('http') ? video.video_url : `${BACKEND_URL}${video.video_url}`;
      const response = await fetch(videoUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `video-${video.id}.mp4`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      setOpenMenu(null);
      toast.success('Видео скачивается...');
    } catch (error) {
      console.error('Download error:', error);
      toast.error('Ошибка при скачивании');
    }
  };

  // Handle video delete
  const handleDelete = async (videoId) => {
    try {
      await axios.delete(`${API}/videos/${videoId}`);
      setUserVideos(prev => prev.filter(v => v.id !== videoId));
      setGeneratingVideos(prev => prev.filter(v => v.id !== videoId));
      setOpenMenu(null);
      toast.success('Видео удалено');
    } catch (error) {
      console.error('Delete error:', error);
      toast.error('Ошибка при удалении');
    }
  };

  // Handle video edit — rename prompt/title
  const handleEdit = async (video) => {
    setOpenMenu(null);
    const currentTitle = video.prompt || video.title || '';
    const newTitle = window.prompt('Новое название видео:', currentTitle);
    if (newTitle === null) return;
    const trimmed = newTitle.trim();
    if (!trimmed || trimmed === currentTitle) return;
    try {
      await axios.patch(`${API}/videos/${video.id}`, { prompt: trimmed });
      setUserVideos(prev => prev.map(v => v.id === video.id ? { ...v, prompt: trimmed } : v));
      setGeneratingVideos(prev => prev.map(v => v.id === video.id ? { ...v, prompt: trimmed, title: trimmed } : v));
      toast.success('Название обновлено');
    } catch (error) {
      console.error('Edit error:', error);
      toast.error('Ошибка при обновлении');
    }
  };

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
        const parsedUser = JSON.parse(savedUser);
        setUser(parsedUser);
        
        // Fetch videos immediately after setting user
        const fetchInitialVideos = async () => {
          const userId = parsedUser.user_id || parsedUser.id;
          if (!userId) return;
          
          console.log('[INIT] Fetching initial videos for', userId);
          setIsLoadingVideos(true);
          
          try {
            const response = await axios.get(`${API}/videos/user/${userId}`);
            const videos = response.data.projects || [];
            console.log('[INIT] Loaded', videos.length, 'videos');
            setUserVideos(videos);
          } catch (error) {
            console.error('[INIT] Failed to fetch:', error);
          } finally {
            setIsLoadingVideos(false);
          }
        };
        
        setTimeout(fetchInitialVideos, 500);
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

  // Fetch user videos when switching to Library tab OR Creations tab OR when user logs in
  useEffect(() => {
    if ((activeMainTab === "Library" || activeMainTab === "Creations") && user) {
      fetchUserVideos();
    }
    // eslint-disable-next-line
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
    if (!user?.user_id && !user?.id) return;
    setIsLoadingVideos(true);
    try {
      const userId = user.user_id || user.id;
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      console.log(`[FETCH_VIDEOS] Fetching for user: ${userId}`);
      
      const response = await axios.get(`${API}/videos/user/${userId}`, {
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      
      const fetchedVideos = response.data.projects || [];
      
      console.log(`[FETCH_VIDEOS] Received ${fetchedVideos.length} videos`);
      
      // Replace userVideos entirely with fresh data from server
      setUserVideos(fetchedVideos);
      
      // Resume polling for any generating videos
      fetchedVideos.forEach(video => {
        if (video.status === 'generating' || video.status === 'processing') {
          const existingGenerating = generatingVideos.find(v => v.id === video.id);
          if (!existingGenerating) {
            setGeneratingVideos(prev => [...prev, { ...video, progress: video.progress || 0 }]);
            pollVideoProgress(video.id);
          }
        }
      });
    } catch (error) {
      if (error.name === 'AbortError') {
        console.error("Fetch videos timeout");
      } else {
        console.error("Failed to fetch videos:", error);
      }
    } finally {
      setIsLoadingVideos(false);
    }
  };

  const pollVideoProgress = (videoId) => {
    let currentProgress = 5;
    let attempts = 0;
    const maxAttempts = 150;
    
    const pollInterval = setInterval(async () => {
      attempts++;
      
      // Increment progress smoothly
      if (currentProgress < 100) {
        const increment = currentProgress < 20 ? 3 : currentProgress < 50 ? 4 : currentProgress < 80 ? 3 : 2;
        currentProgress = Math.min(currentProgress + increment, 100);
      }
      
      try {
        const response = await axios.get(`${API}/video/${videoId}`);
        const videoData = response.data;
        
        setGeneratingVideos(prev => prev.map(v => {
          if (v.id !== videoId) return v;
          
          const newProgress = videoData.status === 'completed' ? 100 : currentProgress;
          
          return {
            ...v,
            ...videoData, // Обновляем ВСЕ данные с сервера (включая created_at)
            progress: Math.max(v.progress || 0, newProgress),
            status: videoData.status
          };
        }));
        
        if (videoData.status === 'completed' || videoData.status === 'failed') {
          clearInterval(pollInterval);
          setGeneratingVideos(prev => prev.filter(v => v.id !== videoId));
          if (videoData.status === 'completed') {
            // Add to userVideos with deduplication
            setUserVideos(prev => {
              const existingIndex = prev.findIndex(v => v.id === videoData.id);
              if (existingIndex >= 0) {
                // Update existing video
                const updated = [...prev];
                updated[existingIndex] = videoData;
                return updated;
              } else {
                // Add new video
                return [videoData, ...prev];
              }
            });
          }
          return;
        }
        
      } catch (error) {
        setGeneratingVideos(prev => prev.map(v => {
          if (v.id !== videoId) return v;
          return {
            ...v,
            progress: Math.max(v.progress || 0, currentProgress)
          };
        }));
      }
      
      if (attempts >= maxAttempts) {
        clearInterval(pollInterval);
        setGeneratingVideos(prev => prev.filter(v => v.id !== videoId));
      }
    }, 1500); // 1.5 seconds for smoother updates
  };

  const handleSubmit = async () => {
    if (!user) {
      navigate('/auth');
      return;
    }
    
    if (!prompt.trim() && attachments.length === 0) return;
    
    const currentPrompt = prompt.trim();
    const currentAttachments = [...attachments];
    
    console.log(`[SUBMIT] Starting: "${currentPrompt}"`);
    
    // Clear input immediately to allow typing next prompt
    setPrompt('');
    setAttachments([]);
    
    try {
      const requestData = {
        prompt: currentPrompt,
        format_id: selectedFormat?.id || "auto",
        language: "auto",
        user_id: user.id || user.user_id
      };
      
      if (currentAttachments.length > 0) {
        const uploadedUrls = [];
        for (const att of currentAttachments) {
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
        
        const videoAttachment = currentAttachments.find(a => a.type === "video");
        if (videoAttachment && uploadedUrls.length > 0) {
          const response = await axios.post(`${API}/device-mockup/create`, {
            video_url: uploadedUrls[0],
            device_type: "phone",
            rotation: 12,
            bg_color: [15, 15, 20],
            animation_style: "camera",
            phone_position: "center",
            aspect_ratio: "9:16",
            user_id: user.user_id || user.id
          });
          
          // Add generating video to the list (БЕЗ created_at - будет взято с сервера)
          const newVideo = {
            id: response.data.id,
            title: currentPrompt,
            prompt: currentPrompt,
            savedAttachments: currentAttachments,
            status: 'generating',
            progress: 0
          };
          setGeneratingVideos(prev => [newVideo, ...prev]);
          
          // Switch to My creations tab
          setActiveMainTab('Creations');
          
          // Scroll to bottom panel
          setTimeout(() => {
            const bottomPanel = document.querySelector('.bottom-panel');
            if (bottomPanel) {
              bottomPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
          }, 100);
          
          toast.success("Создаём 3D анимацию...");
          
          // Poll for progress
          pollVideoProgress(response.data.id);
          return;
        }
        
        requestData.product_images = uploadedUrls;
      }
      
      const response = await axios.post(`${API}/video/generate`, requestData, {
        headers: {
          'Authorization': `Bearer ${user.token}`
        }
      });
      
      console.log(`[SUBMIT] Response ID: ${response.data.id}`);
      
      // Add generating video to the list (БЕЗ created_at - будет взято с сервера)
      const newVideo = {
        id: response.data.id,
        title: currentPrompt,
        prompt: currentPrompt,
        savedAttachments: currentAttachments,
        status: 'generating',
        progress: 5
      };
      
      console.log(`[SUBMIT] Adding to generatingVideos`);
      setGeneratingVideos(prev => [newVideo, ...prev]);
      
      // Switch to My creations tab
      setActiveMainTab('Creations');
      
      // Scroll to bottom panel
      setTimeout(() => {
        const bottomPanel = document.querySelector('.bottom-panel');
        if (bottomPanel) {
          bottomPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
      }, 100);
      
      toast.success("Генерация началась!");
      
      // Poll for progress
      pollVideoProgress(response.data.id);
    } catch (error) {
      console.error("Failed to start generation:", error);
      toast.error("Ошибка при запуске генерации");
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
        onUpgrade={() => { setShowProfile(false); navigate('/upgrade'); }}
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
              onClick={() => navigate("/upgrade")}
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
                <PersonIconAvatar className="header-avatar-icon" />
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
                    <PlusIconSolid className="w-5 h-5" />
                  </button>

                  <div className="input-bottom-right">
                    <button className="input-icon-btn" onClick={() => navigate('/voice')} data-testid="mic-button">
                      <MicIcon className="w-5 h-5" />
                    </button>
                    
                    <button 
                      className={`send-button ${prompt.trim() || attachments.length > 0 ? "active" : ""}`}
                      onClick={handleSubmit}
                      disabled={!prompt.trim() && attachments.length === 0}
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
                  onClick={() => {
                    setActiveMainTab('Creations');
                    if (user) fetchUserVideos();
                  }}
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
                    {/* My Custom Formats Section */}
                    <div className="formats-section-my">
                      <h3 className="formats-section-label">My</h3>
                      {/* Empty state for now */}
                      <div className="my-formats-empty">
                        <p className="no-formats-text">No custom formats</p>
                      </div>
                    </div>

                    {/* All Formats Section */}
                    <div className="formats-section-all">
                      <h3 className="formats-section-label">All</h3>
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
                      <div className="library-loading">
                        <div className="spinner"></div>
                      </div>
                    ) : (generatingVideos.length > 0 || userVideos.length > 0) ? (
                      <div className="creations-grid-real">
                        {generatingVideos.map((video) => (
                          <SmoothProgressCard key={video.id} video={video} onStop={handleStopGeneration} />
                        ))}
                        {userVideos.map((video) => (
                          <div 
                            key={video.id} 
                            className="creation-card"
                            data-testid={`library-video-${video.id}`}
                          >
                            <div 
                              className="creation-card-content"
                              onClick={() => navigate(`/video/${video.id}`)}
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
                            
                            {/* Time ago - bottom left */}
                            <div className="creation-time-ago">
                              {video.status === 'generating' || video.status === 'processing' 
                                ? '' 
                                : getTimeAgo(video.created_at, video.completed_at)}
                            </div>
                            
                            {/* Menu button - bottom right */}
                            <div className="creation-menu-wrapper">
                              <button 
                                className="creation-menu-btn"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  if (openMenu?.id === video.id) {
                                    setOpenMenu(null);
                                  } else {
                                    const btn = e.currentTarget;
                                    const rect = btn.getBoundingClientRect();
                                    const menuHeight = 132;
                                    const menuWidth = 144;
                                    
                                    // Always anchor menu BELOW the button if there's room,
                                    // otherwise place it ABOVE — never both modes alternating mid-scroll.
                                    const spaceBelow = window.innerHeight - rect.bottom;
                                    const placeBelow = spaceBelow >= menuHeight + 12;
                                    const top = placeBelow
                                      ? rect.bottom + 8
                                      : Math.max(10, rect.top - menuHeight - 8);
                                    let left = rect.left + rect.width / 2;
                                    left = Math.min(
                                      Math.max(left, menuWidth / 2 + 10),
                                      window.innerWidth - menuWidth / 2 - 10
                                    );
                                    
                                    setOpenMenu({ id: video.id, top, left });
                                  }
                                }}
                              >
                                <MoreVertical className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="creations-empty-pattern">
                        <div className="creations-pattern-grid">
                          {/* Two columns of squares only */}
                          <div className="pattern-column">
                            <div className="pattern-item ratio-1-1" />
                            <div className="pattern-item ratio-1-1" />
                            <div className="pattern-item ratio-1-1" />
                          </div>
                          <div className="pattern-column">
                            <div className="pattern-item ratio-1-1" />
                            <div className="pattern-item ratio-1-1" />
                            <div className="pattern-item ratio-1-1" />
                          </div>
                        </div>
                        <div className="creations-empty-fade" />
                        <div className="creations-empty-overlay">
                          <p className="creations-empty-text">{t('yourVideosWillBeHere')}</p>
                          <button 
                            className="creations-start-btn"
                            onClick={() => {
                              window.scrollTo({ top: 0, behavior: 'smooth' });
                              setTimeout(() => textareaRef.current?.focus(), 500);
                            }}
                            data-testid="start-create-btn"
                          >
                            <PlusIcon className="start-btn-icon" />
                            {t('start')}
                          </button>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>

        {/* Global dropdown menu (outside grid overflow) */}
        {openMenu && (
          <div 
            className="creation-menu-dropdown"
            style={{
              top: `${openMenu.top}px`,
              left: `${openMenu.left}px`,
              transform: 'translateX(-50%)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <button onClick={(e) => { 
              e.stopPropagation(); 
              const video = userVideos.find(v => v.id === openMenu.id);
              if (video) handleDownload(video); 
              setOpenMenu(null);
            }}>
              <Download className="w-4 h-4" />
              <span>Download</span>
            </button>
            <button onClick={(e) => { 
              e.stopPropagation(); 
              const video = userVideos.find(v => v.id === openMenu.id);
              if (video) handleEdit(video); 
              setOpenMenu(null);
            }}>
              <Edit2 className="w-4 h-4" />
              <span>Edit</span>
            </button>
            <button onClick={(e) => { 
              e.stopPropagation(); 
              handleDelete(openMenu.id); 
              setOpenMenu(null);
            }}>
              <Trash2 className="w-4 h-4" />
              <span>Delete</span>
            </button>
          </div>
        )}

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
      <div className="perspective-grid perspective-grid-mobile">
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
      
      <div className="perspective-grid perspective-grid-desktop">
        <svg viewBox="0 0 400 300" preserveAspectRatio="none" className="grid-svg">
          <line x1="0" y1="0" x2="0" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          <line x1="50" y1="0" x2="50" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          <line x1="100" y1="0" x2="100" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          <line x1="150" y1="0" x2="150" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          <line x1="200" y1="0" x2="200" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          <line x1="250" y1="0" x2="250" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          <line x1="300" y1="0" x2="300" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          <line x1="350" y1="0" x2="350" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          <line x1="400" y1="0" x2="400" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          
          <path d="M0,0 Q200,0 400,0" stroke="rgba(255,255,255,0.06)" strokeWidth="1" fill="none"/>
          <path d="M0,50 Q200,45 400,50" stroke="rgba(255,255,255,0.06)" strokeWidth="1" fill="none"/>
          <path d="M0,100 Q200,90 400,100" stroke="rgba(255,255,255,0.07)" strokeWidth="1" fill="none"/>
          <path d="M0,150 Q200,135 400,150" stroke="rgba(255,255,255,0.08)" strokeWidth="1" fill="none"/>
          <path d="M0,200 Q200,180 400,200" stroke="rgba(255,255,255,0.08)" strokeWidth="1" fill="none"/>
          <path d="M0,250 Q200,225 400,250" stroke="rgba(255,255,255,0.09)" strokeWidth="1" fill="none"/>
          <path d="M0,300 Q200,270 400,300" stroke="rgba(255,255,255,0.1)" strokeWidth="1" fill="none"/>
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
                  onClick={() => navigate('/voice')}
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

        {/* Formats section */}
        <div className="formats-section-new">
          <h2 className="section-title">See formats</h2>
          
          <div className="formats-carousel-wrapper">
            <div className="formats-carousel-inner">
              {FORMATS.slice(0, 6).map((format) => (
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
          
          <button className="formats-start-btn" onClick={() => navigate('/auth')} style={{ display: 'none' }}>
            Start create
          </button>
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
        
        {/* CTA Section */}
        <div className="cta-section">
          <h2 className="cta-title">
            Create <span className="cta-selection-box">
              <span className="sel-line sel-line-top"></span>
              <span className="sel-line sel-line-bottom"></span>
              <span className="sel-line sel-line-left"></span>
              <span className="sel-line sel-line-right"></span>
              <span className="sel-corner sel-corner-tl"></span>
              <span className="sel-corner sel-corner-tr"></span>
              <span className="sel-corner sel-corner-bl"></span>
              <span className="sel-corner sel-corner-br"></span>
              fully edited
            </span> videos
          </h2>
          <p className="cta-subtitle">Turn any prompt into a polished edited video — AI does the rest.</p>
          <button className="cta-get-started-btn" data-testid="cta-get-started-btn">Get started</button>
        </div>
        
        {/* Footer */}
        <footer className="footer-section">
          <div className="footer-card">
            
            <div className="footer-logo">
              <LogoSvg className="footer-logo-svg" />
            </div>
            
            <div className="footer-columns">
              <div className="footer-column">
                <h4 className="footer-column-title">Company</h4>
                <a href="#" className="footer-link">Security</a>
                <a href="#" className="footer-link">Trust Center</a>
                <a href="#" className="footer-link">Press & Media</a>
                <a href="#" className="footer-link">Partnerships</a>
              </div>
              
              <div className="footer-column">
                <h4 className="footer-column-title">Product</h4>
                <a href="#" className="footer-link">Pricing</a>
                <a href="#" className="footer-link">Status</a>
                <a href="#" className="footer-link">Formats</a>
              </div>
              
              <div className="footer-column">
                <h4 className="footer-column-title">Resources</h4>
                <a href="#" className="footer-link">Support</a>
                <a href="#" className="footer-link">Guides & Tutorials</a>
                <a href="#" className="footer-link">Blog</a>
                <a href="#" className="footer-link">FAQs</a>
              </div>
              
              <div className="footer-column">
                <h4 className="footer-column-title">Legal</h4>
                <a href="#" className="footer-link">Privacy policy</a>
                <a href="#" className="footer-link">Do not sell or share my personal information</a>
                <a href="#" className="footer-link">Cookie settings</a>
                <a href="#" className="footer-link">Enterprise terms</a>
                <a href="#" className="footer-link">General terms</a>
                <a href="#" className="footer-link">Platform rules</a>
                <a href="#" className="footer-link">Report abuse</a>
                <a href="#" className="footer-link">Report security concerns</a>
                <a href="#" className="footer-link">DPA</a>
              </div>
              
              <div className="footer-column">
                <h4 className="footer-column-title">Community</h4>
                <a href="#" className="footer-link">Discord</a>
                <a href="#" className="footer-link">TikTok</a>
                <a href="#" className="footer-link">Reddit</a>
                <a href="#" className="footer-link">X (Twitter)</a>
                <a href="#" className="footer-link">YouTube</a>
                <a href="#" className="footer-link">LinkedIn</a>
              </div>
            </div>
          </div>
        </footer>
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
            {/* Show attachments if any */}
            {attachments.length > 0 && (
              <div className="voice-attachments">
                {attachments.map((file, index) => (
                  <div key={index} className="voice-attachment-item">
                    {file.type?.startsWith('video/') ? (
                      <video src={file.preview} muted />
                    ) : (
                      <img src={file.preview} alt="" />
                    )}
                    <button 
                      className="voice-attachment-remove"
                      onClick={() => setAttachments(prev => prev.filter((_, i) => i !== index))}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}
            
            <div className="voice-buttons">
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
        </div>
      )}
    </div>
  );
};

export default MainPage;
