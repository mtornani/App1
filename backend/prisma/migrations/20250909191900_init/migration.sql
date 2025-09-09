-- CreateTable
CREATE TABLE "Player" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "dob" DATETIME,
    "club" TEXT,
    "role" TEXT,
    "nationality" TEXT,
    "residenceHistory" TEXT,
    "track" TEXT,
    "citizenshipStatus" TEXT,
    "natPathFeasibility" TEXT,
    "legalNotes" TEXT,
    "timeToEligibleEstimate" INTEGER,
    "score" INTEGER,
    "rationale" TEXT,
    "sources" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);
